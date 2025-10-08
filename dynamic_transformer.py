"""
Dynamic Multimodal Transformer Architecture

Advanced multimodal AI system
includes dynamic fusion, cross-modal attention, and unified embedding spaces.

Advanced Multi-Modal AI Repository
Date: 10/05/2025
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from dataclasses import dataclass
from enum import Enum


# Configuration Classes
@dataclass
class ModalityConfig:
    """Configuration for each modality"""
    name: str
    input_dim: int
    hidden_dim: int
    num_heads: int
    dropout: float = 0.1
    use_positional_encoding: bool = True


class FusionStrategy(Enum):
    """Fusion strategies for combining modalities"""
    EARLY = "early"      # Combine at input level
    MID = "mid"          # Combine at intermediate representations
    LATE = "late"        # Combine at output level
    DYNAMIC = "dynamic"  # Learn optimal fusion point


class CrossModalAttention(nn.Module):
    """
    Cross-modal attention mechanism for aligning different modalities
    Implements scaled dot-product attention with learnable temperature
    """
    
    def __init__(self, dim: int, num_heads: int = 8, dropout: float = 0.1):
        super().__init__()
        self.dim = dim
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        
        self.q_proj = nn.Linear(dim, dim)
        self.k_proj = nn.Linear(dim, dim)
        self.v_proj = nn.Linear(dim, dim)
        self.out_proj = nn.Linear(dim, dim)
        
        self.dropout = nn.Dropout(dropout)
        self.temperature = nn.Parameter(torch.ones(1))
        
    def forward(
        self, 
        query: torch.Tensor, 
        key: torch.Tensor, 
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        batch_size, seq_len_q, _ = query.shape
        seq_len_kv = key.shape[1]
        
        # Project and reshape for multi-head attention
        Q = self.q_proj(query).view(batch_size, seq_len_q, self.num_heads, self.head_dim)
        K = self.k_proj(key).view(batch_size, seq_len_kv, self.num_heads, self.head_dim)
        V = self.v_proj(value).view(batch_size, seq_len_kv, self.num_heads, self.head_dim)
        
        # Transpose for attention computation
        Q = Q.transpose(1, 2)  # [batch, heads, seq_q, head_dim]
        K = K.transpose(1, 2)  # [batch, heads, seq_kv, head_dim]
        V = V.transpose(1, 2)  # [batch, heads, seq_kv, head_dim]
        
        # Scaled dot-product attention with learnable temperature
        scores = torch.matmul(Q, K.transpose(-2, -1)) / (self.head_dim ** 0.5 * self.temperature)
        
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # Apply attention to values
        context = torch.matmul(attn_weights, V)
        
        # Reshape back
        context = context.transpose(1, 2).contiguous()
        context = context.view(batch_size, seq_len_q, self.dim)
        
        return self.out_proj(context)


class ModalityEncoder(nn.Module):
    """
    Specialized encoder for each modality with modality-specific preprocessing
    """
    
    def __init__(self, config: ModalityConfig):
        super().__init__()
        self.config = config
        
        # Input projection
        self.input_projection = nn.Linear(config.input_dim, config.hidden_dim)
        
        # Positional encoding
        if config.use_positional_encoding:
            self.pos_encoding = nn.Parameter(
                torch.randn(1, 1000, config.hidden_dim) * 0.02
            )
        
        # Transformer layers
        self.layers = nn.ModuleList([
            nn.TransformerEncoderLayer(
                d_model=config.hidden_dim,
                nhead=config.num_heads,
                dim_feedforward=config.hidden_dim * 4,
                dropout=config.dropout,
                activation='gelu',
                batch_first=True
            )
            for _ in range(3)
        ])
        
        self.norm = nn.LayerNorm(config.hidden_dim)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Project input
        x = self.input_projection(x)
        
        # Add positional encoding
        if self.config.use_positional_encoding:
            seq_len = x.shape[1]
            x = x + self.pos_encoding[:, :seq_len, :]
        
        # Apply transformer layers
        for layer in self.layers:
            x = layer(x)
        
        return self.norm(x)


class DynamicFusionModule(nn.Module):
    """
    Dynamic fusion module that learns optimal fusion strategy
    Supports early, mid, late, and dynamic fusion
    """
    
    def __init__(
        self, 
        modality_dims: Dict[str, int],
        output_dim: int,
        strategy: FusionStrategy = FusionStrategy.DYNAMIC
    ):
        super().__init__()
        self.modality_dims = modality_dims
        self.output_dim = output_dim
        self.strategy = strategy
        
        # Projection layers for each modality
        self.projections = nn.ModuleDict({
            name: nn.Linear(dim, output_dim)
            for name, dim in modality_dims.items()
        })
        
        # Fusion gates (for dynamic fusion)
        if strategy == FusionStrategy.DYNAMIC:
            self.fusion_gates = nn.ModuleDict({
                name: nn.Sequential(
                    nn.Linear(dim, 128),
                    nn.ReLU(),
                    nn.Linear(128, 3),  # 3 fusion points (early, mid, late)
                    nn.Softmax(dim=-1)
                )
                for name, dim in modality_dims.items()
            })
        
        # Cross-modal attention for fusion
        self.cross_attention = CrossModalAttention(output_dim)
        
        # Final fusion layer
        self.fusion_layer = nn.Sequential(
            nn.Linear(output_dim * len(modality_dims), output_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(output_dim, output_dim)
        )
        
    def forward(
        self, 
        modality_features: Dict[str, torch.Tensor],
        return_attention: bool = False
    ) -> torch.Tensor:
        
        projected_features = {}
        fusion_weights = {}
        
        # Project each modality to common dimension
        for name, features in modality_features.items():
            projected = self.projections[name](features)
            projected_features[name] = projected
            
            # Calculate fusion weights if using dynamic strategy
            if self.strategy == FusionStrategy.DYNAMIC:
                # Global pooling to get modality representation
                pooled = features.mean(dim=1)
                fusion_weights[name] = self.fusion_gates[name](pooled)
        
        # Combine modalities based on strategy
        if self.strategy == FusionStrategy.EARLY:
            # Simple concatenation and projection
            combined = torch.cat(list(projected_features.values()), dim=-1)
            fused = self.fusion_layer(combined)
            
        elif self.strategy == FusionStrategy.LATE:
            # Pool each modality then combine
            pooled_features = []
            for features in projected_features.values():
                pooled = features.mean(dim=1, keepdim=True)
                pooled_features.append(pooled)
            combined = torch.cat(pooled_features, dim=-1)
            fused = self.fusion_layer(combined)
            
        elif self.strategy == FusionStrategy.MID:
            # Use cross-attention between modalities
            modality_list = list(projected_features.values())
            
            # Each modality attends to all others
            attended_features = []
            for i, (name, features) in enumerate(projected_features.items()):
                # Concatenate all other modalities
                others = torch.cat(
                    [f for j, f in enumerate(modality_list) if j != i], 
                    dim=1
                )
                # Apply cross-modal attention
                attended = self.cross_attention(features, others, others)
                attended_features.append(attended)
            
            combined = torch.cat(attended_features, dim=-1)
            fused = self.fusion_layer(combined)
            
        else:  # DYNAMIC
            # Weighted combination based on learned fusion weights
            fused_features = []
            
            for name, features in projected_features.items():
                weights = fusion_weights[name].unsqueeze(1).unsqueeze(2)
                
                # Apply different fusion strategies with learned weights
                early = features
                mid = self.cross_attention(
                    features, 
                    torch.cat([f for n, f in projected_features.items() if n != name], dim=1),
                    torch.cat([f for n, f in projected_features.items() if n != name], dim=1)
                )
                late = features.mean(dim=1, keepdim=True).expand_as(features)
                
                # Weighted combination
                fused = weights[:, :, 0:1] * early + \
                       weights[:, :, 1:2] * mid + \
                       weights[:, :, 2:3] * late
                       
                fused_features.append(fused)
            
            combined = torch.cat(fused_features, dim=-1)
            fused = self.fusion_layer(combined)
        
        if return_attention and hasattr(self, 'fusion_weights'):
            return fused, fusion_weights
        return fused


class DynamicMultimodalTransformer(nn.Module):
    """
    Main Dynamic Multimodal Transformer architecture
    Supports multiple modalities with dynamic fusion and cross-modal reasoning
    """
    
    def __init__(
        self,
        modality_configs: Dict[str, ModalityConfig],
        hidden_dim: int = 768,
        num_classes: Optional[int] = None,
        fusion_strategy: FusionStrategy = FusionStrategy.DYNAMIC,
        use_mixture_of_experts: bool = False
    ):
        super().__init__()
        
        self.modality_configs = modality_configs
        self.hidden_dim = hidden_dim
        self.num_classes = num_classes
        
        # Create encoders for each modality
        self.encoders = nn.ModuleDict({
            name: ModalityEncoder(config)
            for name, config in modality_configs.items()
        })
        
        # Dynamic fusion module
        encoder_dims = {
            name: config.hidden_dim 
            for name, config in modality_configs.items()
        }
        self.fusion = DynamicFusionModule(
            encoder_dims, 
            hidden_dim, 
            fusion_strategy
        )
        
        # Mixture of Experts (optional)
        if use_mixture_of_experts:
            self.moe = MixtureOfExperts(hidden_dim, num_experts=len(modality_configs))
        else:
            self.moe = None
        
        # Final transformer layers for reasoning
        self.reasoning_layers = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
                d_model=hidden_dim,
                nhead=8,
                dim_feedforward=hidden_dim * 4,
                dropout=0.1,
                activation='gelu',
                batch_first=True
            ),
            num_layers=3
        )
        
        # Output head
        if num_classes is not None:
            self.classifier = nn.Sequential(
                nn.LayerNorm(hidden_dim),
                nn.Dropout(0.1),
                nn.Linear(hidden_dim, num_classes)
            )
        else:
            self.classifier = None
        
        # Learnable CLS token for classification
        self.cls_token = nn.Parameter(torch.randn(1, 1, hidden_dim))
        
    def forward(
        self,
        inputs: Dict[str, torch.Tensor],
        return_embeddings: bool = False
    ) -> Dict[str, torch.Tensor]:
        
        batch_size = next(iter(inputs.values())).shape[0]
        
        # Encode each modality
        encoded_features = {}
        for name, input_tensor in inputs.items():
            if name in self.encoders:
                encoded = self.encoders[name](input_tensor)
                encoded_features[name] = encoded
        
        # Apply dynamic fusion
        fused_features = self.fusion(encoded_features)
        
        # Add CLS token
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        fused_with_cls = torch.cat([cls_tokens, fused_features], dim=1)
        
        # Apply mixture of experts if enabled
        if self.moe is not None:
            fused_with_cls = self.moe(fused_with_cls)
        
        # Apply reasoning layers
        output_features = self.reasoning_layers(fused_with_cls)
        
        # Get CLS token output
        cls_output = output_features[:, 0]
        
        results = {
            "embeddings": cls_output,
            "sequence_output": output_features
        }
        
        # Classification if needed
        if self.classifier is not None:
            logits = self.classifier(cls_output)
            results["logits"] = logits
        
        if return_embeddings:
            results["modality_embeddings"] = encoded_features
        
        return results


class MixtureOfExperts(nn.Module):
    """
    Mixture of Experts module for specialized processing
    Each expert specializes in different modality combinations
    """
    
    def __init__(self, dim: int, num_experts: int = 4):
        super().__init__()
        self.dim = dim
        self.num_experts = num_experts
        
        # Expert networks
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(dim, dim * 2),
                nn.GELU(),
                nn.Dropout(0.1),
                nn.Linear(dim * 2, dim)
            )
            for _ in range(num_experts)
        ])
        
        # Gating network
        self.gate = nn.Sequential(
            nn.Linear(dim, dim // 2),
            nn.ReLU(),
            nn.Linear(dim // 2, num_experts),
            nn.Softmax(dim=-1)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len, _ = x.shape
        
        # Calculate gating weights
        x_pooled = x.mean(dim=1)  # Pool over sequence
        gate_weights = self.gate(x_pooled)  # [batch, num_experts]
        
        # Apply experts
        expert_outputs = []
        for expert in self.experts:
            expert_out = expert(x)
            expert_outputs.append(expert_out)
        
        # Stack expert outputs
        expert_outputs = torch.stack(expert_outputs, dim=1)  # [batch, experts, seq, dim]
        
        # Apply gating weights
        gate_weights = gate_weights.unsqueeze(2).unsqueeze(3)  # [batch, experts, 1, 1]
        mixed_output = (expert_outputs * gate_weights).sum(dim=1)
        
        return mixed_output


# Utility functions
def create_multimodal_model(
    text_dim: int = 768,
    image_dim: int = 2048,
    audio_dim: int = 128,
    num_classes: int = 10,
    fusion_strategy: str = "dynamic"
) -> DynamicMultimodalTransformer:
    """
    Factory function to create a multimodal model with common configurations
    """
    
    configs = {
        "text": ModalityConfig("text", text_dim, 512, 8),
        "image": ModalityConfig("image", image_dim, 512, 8),
        "audio": ModalityConfig("audio", audio_dim, 512, 8)
    }
    
    strategy_map = {
        "early": FusionStrategy.EARLY,
        "mid": FusionStrategy.MID,
        "late": FusionStrategy.LATE,
        "dynamic": FusionStrategy.DYNAMIC
    }
    
    model = DynamicMultimodalTransformer(
        modality_configs=configs,
        hidden_dim=768,
        num_classes=num_classes,
        fusion_strategy=strategy_map[fusion_strategy],
        use_mixture_of_experts=True
    )
    
    return model


# Example usage
if __name__ == "__main__":
    # Create model
    model = create_multimodal_model(
        text_dim=768,
        image_dim=2048,
        audio_dim=128,
        num_classes=10,
        fusion_strategy="dynamic"
    )
    
    # Create dummy inputs
    batch_size = 4
    inputs = {
        "text": torch.randn(batch_size, 50, 768),    # [batch, seq_len, dim]
        "image": torch.randn(batch_size, 196, 2048), # [batch, patches, dim]
        "audio": torch.randn(batch_size, 100, 128)   # [batch, frames, dim]
    }
    
    # Forward pass
    outputs = model(inputs, return_embeddings=True)
    
    print(f"Model created with {sum(p.numel() for p in model.parameters())} parameters")
    print(f"Output keys: {outputs.keys()}")
    print(f"Logits shape: {outputs['logits'].shape}")
    print(f"Embeddings shape: {outputs['embeddings'].shape}")
    
    # Print modality embeddings shapes
    for modality, embedding in outputs['modality_embeddings'].items():
        print(f"{modality} embedding shape: {embedding.shape}")
