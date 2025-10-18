"""
Surgical Fine-Tuning Framework for Mixture-of-Experts Models
Author: Cazzy Aporbo
Focus: Layer-wise adaptation, model merging, and routing optimization
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from torch.cuda.amp import autocast, GradScaler
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp.wrap import transformer_auto_wrap_policy
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
import json
import math
from pathlib import Path
from collections import OrderedDict, defaultdict
import hashlib
from contextlib import contextmanager
import warnings
import einops
from einops import rearrange, repeat
import transformers
from transformers import (
    MistralForCausalLM,
    MistralConfig,
    AutoTokenizer,
    AutoModelForCausalLM
)
from safetensors import safe_open
from safetensors.torch import save_file
import datasets
from accelerate import init_empty_weights, load_checkpoint_and_dispatch
from functools import partial
import copy
import gc


@dataclass
class SurgicalConfig:
    """Configuration for surgical fine-tuning with advanced techniques"""
    
    base_model: str = "mistralai/Mixtral-8x7B-v0.1"
    target_layers: List[int] = None  # None means all layers
    
    # Layer-wise learning rates
    use_layer_wise_lr_decay: bool = True
    lr_decay_rate: float = 0.9
    base_learning_rate: float = 1e-5
    min_learning_rate: float = 1e-7
    
    # DoRA configuration (Weight-Decomposed Low-Rank Adaptation)
    use_dora: bool = True
    dora_rank: int = 128
    dora_magnitude_scale: float = 1.0
    dora_direction_scale: float = 0.1
    
    # LASER configuration (Layer-Selective Rank Reduction)
    use_laser: bool = True
    laser_rank_reduction: Dict[int, int] = None  # {layer_idx: target_rank}
    laser_warmup_steps: int = 100
    
    # Model Soups configuration
    use_model_soups: bool = True
    soup_ingredients: List[str] = None  # Paths to models to merge
    soup_mixing_weights: List[float] = None
    soup_strategy: str = "greedy"  # greedy, uniform, learned
    
    # MoE routing optimization
    optimize_router: bool = True
    router_z_loss_weight: float = 0.001
    router_aux_loss_weight: float = 0.001
    expert_capacity_factor: float = 1.25
    
    # DARE (Drop And REscale) merging
    use_dare: bool = True
    dare_drop_rate: float = 0.5
    dare_rescale: bool = True
    
    # Mixture of LoRA experts
    use_mixture_of_loras: bool = True
    num_lora_experts: int = 4
    lora_expert_routing: str = "learned"  # learned, random, deterministic
    
    # Training configuration
    micro_batch_size: int = 1
    gradient_accumulation: int = 32
    num_epochs: int = 1
    max_grad_norm: float = 0.5
    warmup_ratio: float = 0.03
    
    # Memory optimization
    use_activation_checkpointing: bool = True
    use_cpu_offload: bool = False
    use_optimizer_offload: bool = True
    
    # Precision
    compute_dtype: str = "bfloat16"
    use_tf32: bool = True
    
    # Evaluation
    eval_every_n_steps: int = 50
    save_every_n_steps: int = 200
    
    # Output
    output_dir: str = "./surgical_finetuned"
    merge_adapter_into_base: bool = True
    
    def __post_init__(self):
        if self.target_layers is None:
            self.target_layers = list(range(32))  # Default for Mixtral
        if self.laser_rank_reduction is None:
            self.laser_rank_reduction = {i: max(256, 1024 - i * 20) for i in range(32)}


class DoRALayer(nn.Module):
    """Weight-Decomposed Low-Rank Adaptation layer"""
    
    def __init__(
        self, 
        in_features: int, 
        out_features: int, 
        rank: int = 16,
        magnitude_scale: float = 1.0,
        direction_scale: float = 0.1,
        dropout: float = 0.0
    ):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.rank = rank
        
        # Magnitude and direction components
        self.magnitude = nn.Parameter(torch.ones(out_features))
        self.lora_A = nn.Linear(in_features, rank, bias=False)
        self.lora_B = nn.Linear(rank, out_features, bias=False)
        self.lora_dropout = nn.Dropout(dropout)
        
        # Scaling factors
        self.magnitude_scale = magnitude_scale
        self.direction_scale = direction_scale
        
        # Initialize
        nn.init.kaiming_uniform_(self.lora_A.weight, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B.weight)
        
    def forward(self, x: torch.Tensor, base_weight: torch.Tensor) -> torch.Tensor:
        # Compute base output
        base_output = F.linear(x, base_weight)
        
        # Compute LoRA update
        lora_output = self.lora_B(self.lora_dropout(self.lora_A(x)))
        
        # Decompose into magnitude and direction
        weight_norm = torch.norm(base_weight, dim=1, keepdim=True)
        weight_direction = base_weight / (weight_norm + 1e-6)
        
        # Apply magnitude scaling
        scaled_magnitude = self.magnitude * self.magnitude_scale
        magnitude_output = base_output * scaled_magnitude.unsqueeze(0)
        
        # Combine with directional update
        final_output = magnitude_output + lora_output * self.direction_scale
        
        return final_output


class LASERSurgery(nn.Module):
    """Layer-Selective Rank Reduction module"""
    
    def __init__(self, layer_idx: int, target_rank: int, warmup_steps: int = 100):
        super().__init__()
        self.layer_idx = layer_idx
        self.target_rank = target_rank
        self.warmup_steps = warmup_steps
        self.current_step = 0
        
    def apply_laser(self, weight: torch.Tensor) -> torch.Tensor:
        """Apply LASER rank reduction to weight matrix"""
        
        # Gradually reduce rank during warmup
        if self.current_step < self.warmup_steps:
            reduction_ratio = self.current_step / self.warmup_steps
            current_rank = int(weight.shape[0] - 
                              (weight.shape[0] - self.target_rank) * reduction_ratio)
        else:
            current_rank = self.target_rank
        
        # SVD-based rank reduction
        U, S, V = torch.svd_lowrank(weight, q=current_rank)
        
        # Reconstruct with reduced rank
        weight_reduced = U @ torch.diag(S) @ V.T
        
        self.current_step += 1
        return weight_reduced


class MixtureOfLoRAExperts(nn.Module):
    """Multiple LoRA experts with learned routing"""
    
    def __init__(
        self,
        in_features: int,
        out_features: int,
        num_experts: int = 4,
        rank: int = 16,
        routing_strategy: str = "learned"
    ):
        super().__init__()
        self.num_experts = num_experts
        self.routing_strategy = routing_strategy
        
        # Create multiple LoRA experts
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(in_features, rank, bias=False),
                nn.Linear(rank, out_features, bias=False)
            ) for _ in range(num_experts)
        ])
        
        # Router network
        if routing_strategy == "learned":
            self.router = nn.Linear(in_features, num_experts)
        
        # Initialize experts differently
        for i, expert in enumerate(self.experts):
            nn.init.kaiming_uniform_(expert[0].weight, a=math.sqrt(5))
            nn.init.zeros_(expert[1].weight)
            # Add noise for diversity
            expert[1].weight.data += torch.randn_like(expert[1].weight) * 0.01 * (i + 1)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size = x.shape[0]
        
        if self.routing_strategy == "learned":
            # Compute routing weights
            router_logits = self.router(x.mean(dim=1))  # Pool sequence dimension
            routing_weights = F.softmax(router_logits, dim=-1)
            
            # Compute expert outputs
            expert_outputs = []
            for i, expert in enumerate(self.experts):
                expert_out = expert[1](expert[0](x))
                expert_outputs.append(expert_out * routing_weights[:, i:i+1].unsqueeze(1))
            
            # Combine expert outputs
            output = sum(expert_outputs)
            
            # Compute auxiliary losses for load balancing
            self.z_loss = torch.mean(torch.logsumexp(router_logits, dim=-1) ** 2)
            self.aux_loss = torch.mean(routing_weights.max(dim=-1)[0])
            
        else:  # Random or deterministic routing
            expert_idx = torch.randint(0, self.num_experts, (1,)).item()
            output = self.experts[expert_idx][1](self.experts[expert_idx][0](x))
            self.z_loss = torch.tensor(0.0)
            self.aux_loss = torch.tensor(0.0)
        
        return output


class ModelSoupMixer:
    """Advanced model merging using various strategies"""
    
    def __init__(self, strategy: str = "greedy"):
        self.strategy = strategy
        self.mixing_history = []
        
    def merge_models(
        self,
        models: List[Dict[str, torch.Tensor]],
        weights: Optional[List[float]] = None,
        use_dare: bool = False,
        dare_drop_rate: float = 0.5
    ) -> Dict[str, torch.Tensor]:
        """Merge multiple model checkpoints"""
        
        if weights is None:
            weights = [1.0 / len(models)] * len(models)
        
        merged = {}
        
        for key in models[0].keys():
            if "weight" in key:
                if use_dare:
                    # DARE merging: Drop And REscale
                    tensors = []
                    for model, w in zip(models, weights):
                        mask = torch.bernoulli(
                            torch.ones_like(model[key]) * (1 - dare_drop_rate)
                        )
                        rescaled = model[key] * mask / (1 - dare_drop_rate)
                        tensors.append(rescaled * w)
                    merged[key] = sum(tensors)
                elif self.strategy == "greedy":
                    # Greedy soup: select best performing weight
                    merged[key] = self._greedy_select(models, key, weights)
                elif self.strategy == "uniform":
                    # Uniform averaging
                    merged[key] = sum(m[key] * w for m, w in zip(models, weights))
                elif self.strategy == "fisher":
                    # Fisher-weighted averaging
                    merged[key] = self._fisher_merge(models, key)
                else:
                    merged[key] = models[0][key]
            else:
                # Non-weight parameters (buffers, etc.)
                merged[key] = models[0][key]
        
        return merged
    
    def _greedy_select(
        self, 
        models: List[Dict], 
        key: str, 
        weights: List[float]
    ) -> torch.Tensor:
        """Greedy selection based on magnitude"""
        magnitudes = [torch.norm(m[key]).item() for m in models]
        best_idx = magnitudes.index(max(magnitudes))
        return models[best_idx][key]
    
    def _fisher_merge(self, models: List[Dict], key: str) -> torch.Tensor:
        """Fisher information weighted merging"""
        # Simplified Fisher approximation using gradient magnitudes
        fisher_weights = []
        for model in models:
            if model[key].grad is not None:
                fisher_weights.append(torch.abs(model[key].grad).mean().item())
            else:
                fisher_weights.append(1.0)
        
        total = sum(fisher_weights)
        normalized = [f / total for f in fisher_weights]
        
        return sum(m[key] * w for m, w in zip(models, normalized))


class SurgicalFineTuner:
    """Main class for surgical fine-tuning with advanced techniques"""
    
    def __init__(self, config: SurgicalConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Enable TF32 for Ampere GPUs
        if config.use_tf32:
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
        
        # Load model and tokenizer
        self._load_model_and_tokenizer()
        
        # Apply surgical modifications
        self._apply_surgical_modifications()
        
        # Initialize optimizer with layer-wise LR
        self._init_optimizer()
        
        # Initialize gradient scaler
        self.scaler = GradScaler()
        
        # Model soup mixer
        self.soup_mixer = ModelSoupMixer(config.soup_strategy)
        
        # Metrics tracking
        self.metrics = defaultdict(list)
        
    def _load_model_and_tokenizer(self):
        """Load base model with memory optimization"""
        
        print(f"Loading model: {self.config.base_model}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.config.base_model)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load model with memory mapping
        dtype = getattr(torch, self.config.compute_dtype)
        
        with init_empty_weights():
            config = transformers.AutoConfig.from_pretrained(self.config.base_model)
            self.model = AutoModelForCausalLM.from_config(config)
        
        # Load checkpoint with device mapping
        self.model = load_checkpoint_and_dispatch(
            self.model,
            self.config.base_model,
            device_map="auto",
            dtype=dtype,
            offload_folder="./offload" if self.config.use_cpu_offload else None
        )
        
    def _apply_surgical_modifications(self):
        """Apply layer-specific modifications"""
        
        print("Applying surgical modifications...")
        
        # Track modifications
        self.modifications = {}
        
        for layer_idx in self.config.target_layers:
            layer = self._get_layer(layer_idx)
            
            # Apply DoRA
            if self.config.use_dora:
                self._apply_dora_to_layer(layer, layer_idx)
            
            # Apply LASER
            if self.config.use_laser:
                self._apply_laser_to_layer(layer, layer_idx)
            
            # Apply Mixture of LoRA Experts
            if self.config.use_mixture_of_loras:
                self._apply_mixture_of_loras(layer, layer_idx)
            
            # Enable gradient checkpointing selectively
            if self.config.use_activation_checkpointing:
                if layer_idx % 2 == 0:  # Checkpoint every other layer
                    layer.gradient_checkpointing = True
        
        # Freeze non-target layers
        self._selective_freezing()
        
    def _get_layer(self, layer_idx: int):
        """Get specific layer from model"""
        if hasattr(self.model, 'model'):
            return self.model.model.layers[layer_idx]
        return self.model.layers[layer_idx]
    
    def _apply_dora_to_layer(self, layer, layer_idx: int):
        """Apply DoRA to a specific layer"""
        
        # Replace attention projections with DoRA
        if hasattr(layer.self_attn, 'q_proj'):
            original_weight = layer.self_attn.q_proj.weight
            dora = DoRALayer(
                original_weight.shape[1],
                original_weight.shape[0],
                rank=self.config.dora_rank,
                magnitude_scale=self.config.dora_magnitude_scale,
                direction_scale=self.config.dora_direction_scale
            )
            
            # Custom forward function
            def dora_forward(self, x):
                return dora(x, original_weight)
            
            layer.self_attn.q_proj.forward = partial(dora_forward, layer.self_attn.q_proj)
            self.modifications[f"layer_{layer_idx}_q_proj"] = dora
    
    def _apply_laser_to_layer(self, layer, layer_idx: int):
        """Apply LASER rank reduction to a layer"""
        
        if layer_idx in self.config.laser_rank_reduction:
            target_rank = self.config.laser_rank_reduction[layer_idx]
            laser = LASERSurgery(layer_idx, target_rank, self.config.laser_warmup_steps)
            
            # Apply to FFN weights
            if hasattr(layer, 'mlp'):
                original_gate = layer.mlp.gate_proj.weight.data
                layer.mlp.gate_proj.weight.data = laser.apply_laser(original_gate)
                
            self.modifications[f"layer_{layer_idx}_laser"] = laser
    
    def _apply_mixture_of_loras(self, layer, layer_idx: int):
        """Apply Mixture of LoRA Experts to a layer"""
        
        if hasattr(layer.self_attn, 'v_proj'):
            original_v_proj = layer.self_attn.v_proj
            
            moe_lora = MixtureOfLoRAExperts(
                original_v_proj.in_features,
                original_v_proj.out_features,
                num_experts=self.config.num_lora_experts,
                rank=16,
                routing_strategy=self.config.lora_expert_routing
            )
            
            # Combine with original projection
            def moe_forward(self, x):
                base_out = F.linear(x, original_v_proj.weight)
                lora_out = moe_lora(x)
                return base_out + lora_out
            
            layer.self_attn.v_proj.forward = partial(moe_forward, layer.self_attn.v_proj)
            self.modifications[f"layer_{layer_idx}_moe_lora"] = moe_lora
    
    def _selective_freezing(self):
        """Selectively freeze layers not being fine-tuned"""
        
        for name, param in self.model.named_parameters():
            # Determine if parameter should be frozen
            should_train = False
            
            for layer_idx in self.config.target_layers:
                if f"layers.{layer_idx}" in name:
                    should_train = True
                    break
            
            # Always train added modules
            if any(mod in name for mod in ["dora", "lora", "router"]):
                should_train = True
            
            param.requires_grad = should_train
        
        # Count trainable parameters
        trainable = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in self.model.parameters())
        print(f"Trainable parameters: {trainable:,} / {total:,} ({trainable/total*100:.2f}%)")
    
    def _init_optimizer(self):
        """Initialize optimizer with layer-wise learning rates"""
        
        param_groups = []
        
        if self.config.use_layer_wise_lr_decay:
            # Create parameter groups with layer-wise LR decay
            for layer_idx in range(len(self.config.target_layers)):
                layer_params = []
                layer_lr = self.config.base_learning_rate * (
                    self.config.lr_decay_rate ** layer_idx
                )
                layer_lr = max(layer_lr, self.config.min_learning_rate)
                
                for name, param in self.model.named_parameters():
                    if param.requires_grad and f"layers.{layer_idx}" in name:
                        layer_params.append(param)
                
                if layer_params:
                    param_groups.append({
                        'params': layer_params,
                        'lr': layer_lr,
                        'layer_idx': layer_idx
                    })
            
            # Add non-layer parameters
            other_params = []
            for name, param in self.model.named_parameters():
                if param.requires_grad and not any(f"layers.{i}" in name for i in range(32)):
                    other_params.append(param)
            
            if other_params:
                param_groups.append({
                    'params': other_params,
                    'lr': self.config.base_learning_rate
                })
        else:
            # Standard single learning rate
            param_groups = [
                {'params': [p for p in self.model.parameters() if p.requires_grad]}
            ]
        
        # Initialize optimizer
        self.optimizer = AdamW(
            param_groups,
            lr=self.config.base_learning_rate,
            weight_decay=0.01,
            betas=(0.9, 0.95),
            eps=1e-8
        )
    
    def train_step(self, batch: Dict[str, torch.Tensor]) -> Dict[str, float]:
        """Single training step with advanced techniques"""
        
        self.model.train()
        
        # Move batch to device
        batch = {k: v.to(self.device) for k, v in batch.items()}
        
        # Mixed precision forward pass
        with autocast(dtype=getattr(torch, self.config.compute_dtype)):
            outputs = self.model(**batch)
            loss = outputs.loss
            
            # Add auxiliary losses
            total_aux_loss = 0
            for name, module in self.modifications.items():
                if isinstance(module, MixtureOfLoRAExperts):
                    total_aux_loss += (
                        module.z_loss * self.config.router_z_loss_weight +
                        module.aux_loss * self.config.router_aux_loss_weight
                    )
            
            loss = loss + total_aux_loss
        
        # Backward pass with gradient scaling
        self.scaler.scale(loss).backward()
        
        # Gradient clipping
        self.scaler.unscale_(self.optimizer)
        torch.nn.utils.clip_grad_norm_(
            self.model.parameters(), 
            self.config.max_grad_norm
        )
        
        # Optimizer step
        self.scaler.step(self.optimizer)
        self.scaler.update()
        self.optimizer.zero_grad()
        
        # Track metrics
        metrics = {
            'loss': loss.item(),
            'aux_loss': total_aux_loss.item() if isinstance(total_aux_loss, torch.Tensor) else total_aux_loss,
            'grad_norm': self._compute_grad_norm(),
            'learning_rate': self.optimizer.param_groups[0]['lr']
        }
        
        return metrics
    
    def _compute_grad_norm(self) -> float:
        """Compute total gradient norm"""
        total_norm = 0.0
        for p in self.model.parameters():
            if p.grad is not None:
                param_norm = p.grad.detach().data.norm(2)
                total_norm += param_norm.item() ** 2
        return total_norm ** 0.5
    
    def merge_checkpoints(self, checkpoint_paths: List[str]) -> Dict[str, torch.Tensor]:
        """Merge multiple checkpoints using configured strategy"""
        
        models = []
        for path in checkpoint_paths:
            with safe_open(path, framework="pt") as f:
                state_dict = {key: f.get_tensor(key) for key in f.keys()}
                models.append(state_dict)
        
        merged = self.soup_mixer.merge_models(
            models,
            weights=self.config.soup_mixing_weights,
            use_dare=self.config.use_dare,
            dare_drop_rate=self.config.dare_drop_rate
        )
        
        return merged
    
    def save_checkpoint(self, path: str, merge_adapter: bool = False):
        """Save model checkpoint with optional adapter merging"""
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        if merge_adapter and self.config.merge_adapter_into_base:
            # Merge LoRA/DoRA weights into base model
            merged_state_dict = self._merge_adapters()
            save_file(merged_state_dict, path)
        else:
            # Save adapter weights separately
            adapter_state_dict = {}
            for name, module in self.modifications.items():
                if hasattr(module, 'state_dict'):
                    for key, value in module.state_dict().items():
                        adapter_state_dict[f"{name}.{key}"] = value
            
            save_file(adapter_state_dict, path.replace('.safetensors', '_adapter.safetensors'))
    
    def _merge_adapters(self) -> Dict[str, torch.Tensor]:
        """Merge adapter weights into base model"""
        
        merged_state_dict = self.model.state_dict()
        
        # Merge DoRA weights
        for name, module in self.modifications.items():
            if isinstance(module, DoRALayer):
                # Complex merging logic for DoRA
                layer_idx = int(name.split('_')[1])
                layer = self._get_layer(layer_idx)
                
                if 'q_proj' in name:
                    original_weight = layer.self_attn.q_proj.weight
                    lora_weight = module.lora_B.weight @ module.lora_A.weight
                    magnitude_scaling = module.magnitude * module.magnitude_scale
                    
                    # Merge weights
                    merged_weight = original_weight * magnitude_scaling.unsqueeze(1)
                    merged_weight += lora_weight * module.direction_scale
                    
                    merged_state_dict[f"model.layers.{layer_idx}.self_attn.q_proj.weight"] = merged_weight
        
        return merged_state_dict
    
    def run_training(self, train_dataloader: DataLoader, eval_dataloader: Optional[DataLoader] = None):
        """Main training loop"""
        
        global_step = 0
        best_eval_loss = float('inf')
        
        num_training_steps = len(train_dataloader) * self.config.num_epochs
        num_warmup_steps = int(num_training_steps * self.config.warmup_ratio)
        
        print(f"Starting training for {num_training_steps} steps")
        
        for epoch in range(self.config.num_epochs):
            print(f"\nEpoch {epoch + 1}/{self.config.num_epochs}")
            
            epoch_metrics = defaultdict(list)
            
            for batch_idx, batch in enumerate(train_dataloader):
                # Training step
                metrics = self.train_step(batch)
                
                # Track metrics
                for key, value in metrics.items():
                    epoch_metrics[key].append(value)
                
                # Learning rate scheduling (linear warmup + cosine decay)
                if global_step < num_warmup_steps:
                    lr_scale = global_step / num_warmup_steps
                else:
                    progress = (global_step - num_warmup_steps) / (num_training_steps - num_warmup_steps)
                    lr_scale = 0.5 * (1 + math.cos(math.pi * progress))
                
                for param_group in self.optimizer.param_groups:
                    if 'layer_idx' in param_group:
                        base_lr = self.config.base_learning_rate * (
                            self.config.lr_decay_rate ** param_group['layer_idx']
                        )
                    else:
                        base_lr = self.config.base_learning_rate
                    param_group['lr'] = base_lr * lr_scale
                
                # Logging
                if global_step % 10 == 0:
                    avg_loss = np.mean(epoch_metrics['loss'][-10:])
                    print(f"Step {global_step}: Loss = {avg_loss:.4f}, LR = {metrics['learning_rate']:.2e}")
                
                # Evaluation
                if eval_dataloader and global_step % self.config.eval_every_n_steps == 0:
                    eval_loss = self.evaluate(eval_dataloader)
                    print(f"Eval Loss: {eval_loss:.4f}")
                    
                    if eval_loss < best_eval_loss:
                        best_eval_loss = eval_loss
                        self.save_checkpoint(
                            f"{self.config.output_dir}/best_model.safetensors",
                            merge_adapter=True
                        )
                
                # Save checkpoint
                if global_step % self.config.save_every_n_steps == 0:
                    self.save_checkpoint(
                        f"{self.config.output_dir}/checkpoint_{global_step}.safetensors"
                    )
                
                global_step += 1
            
            # End of epoch summary
            print(f"\nEpoch {epoch + 1} Summary:")
            for key, values in epoch_metrics.items():
                print(f"  {key}: {np.mean(values):.4f}")
        
        # Final save
        self.save_checkpoint(
            f"{self.config.output_dir}/final_model.safetensors",
            merge_adapter=True
        )
        
        print("\nTraining completed successfully")
    
    def evaluate(self, eval_dataloader: DataLoader) -> float:
        """Evaluation loop"""
        
        self.model.eval()
        total_loss = 0
        num_batches = 0
        
        with torch.no_grad():
            for batch in eval_dataloader:
                batch = {k: v.to(self.device) for k, v in batch.items()}
                
                with autocast(dtype=getattr(torch, self.config.compute_dtype)):
                    outputs = self.model(**batch)
                    total_loss += outputs.loss.item()
                    num_batches += 1
        
        self.model.train()
        return total_loss / num_batches


def main():
    """Main execution"""
    
    # Configure surgical fine-tuning
    config = SurgicalConfig(
        base_model="mistralai/Mixtral-8x7B-v0.1",
        target_layers=[10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],  # Middle layers
        use_dora=True,
        use_laser=True,
        use_mixture_of_loras=True,
        use_model_soups=True,
        use_dare=True,
        dora_rank=128,
        num_lora_experts=4,
        base_learning_rate=1e-5,
        use_layer_wise_lr_decay=True,
        num_epochs=1,
        output_dir="./surgical_mixtral_finetuned"
    )
    
    print("Initializing Surgical Fine-Tuner")
    print("-" * 50)
    
    tuner = SurgicalFineTuner(config)
    
    # Load your dataset here
    # train_dataloader = ...
    # eval_dataloader = ...
    
    # Example with dummy data
    class DummyDataset(Dataset):
        def __init__(self, size=1000):
            self.size = size
        
        def __len__(self):
            return self.size
        
        def __getitem__(self, idx):
            return {
                'input_ids': torch.randint(0, 32000, (512,)),
                'attention_mask': torch.ones(512),
                'labels': torch.randint(0, 32000, (512,))
            }
    
    train_dataset = DummyDataset(1000)
    train_dataloader = DataLoader(train_dataset, batch_size=config.micro_batch_size, shuffle=True)
    
    eval_dataset = DummyDataset(100)
    eval_dataloader = DataLoader(eval_dataset, batch_size=config.micro_batch_size)
    
    # Run training
    tuner.run_training(train_dataloader, eval_dataloader)
    
    # Merge checkpoints if multiple runs
    if config.soup_ingredients:
        print("\nMerging model checkpoints using Model Soups")
        merged = tuner.merge_checkpoints(config.soup_ingredients)
        save_file(merged, f"{config.output_dir}/merged_final.safetensors")


if __name__ == "__main__":
    main()
