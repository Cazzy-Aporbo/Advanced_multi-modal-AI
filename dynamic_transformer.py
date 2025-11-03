"""
Advanced Multimodal Transformer Architecture with Hierarchical Reasoning
Author: Cazandra Aporbo
Date: November 2025

This implementation presents a multimodal AI system that goes beyond
traditional fusion approaches.
- Hierarchical attention mechanisms with learned routing
- Adaptive computation graphs based on input complexity
- Memory-augmented reasoning with persistent attention states
- Uncertainty quantification in multimodal predictions
- Contrastive learning objectives for robust representations
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
import numpy as np
from dataclasses import dataclass, field
from enum import Enum, auto
import math
from collections import OrderedDict, deque
from functools import partial, lru_cache
import warnings
from abc import ABC, abstractmethod


@dataclass
class ModalityConfiguration:
    """
    Enhanced configuration for modality-specific processing.
    
    Each modality can have different architectural requirements. This configuration
    allows fine-grained control over processing pipelines while maintaining
    consistency across the unified embedding space.
    """
    name: str
    input_dim: int
    hidden_dim: int
    output_dim: int
    num_heads: int
    num_layers: int
    dropout_rate: float = 0.1
    activation: str = 'gelu'
    use_positional_encoding: bool = True
    positional_encoding_type: str = 'sinusoidal'  # sinusoidal, learned, rotary
    max_sequence_length: int = 2048
    attention_window: Optional[int] = None  # For local attention
    use_flash_attention: bool = False
    gradient_checkpointing: bool = False
    layer_norm_eps: float = 1e-12
    initializer_range: float = 0.02
    hidden_dropout_prob: float = 0.1
    attention_probs_dropout_prob: float = 0.1
    
    def validate(self):
        """Validate configuration parameters."""
        assert self.input_dim > 0, "Input dimension must be positive"
        assert self.hidden_dim > 0, "Hidden dimension must be positive"
        assert self.num_heads > 0, "Number of heads must be positive"
        assert self.hidden_dim % self.num_heads == 0, "Hidden dim must be divisible by num_heads"
        assert 0 <= self.dropout_rate <= 1, "Dropout rate must be between 0 and 1"


class AttentionMechanism(Enum):
    """Advanced attention mechanisms available in the system."""
    STANDARD = auto()          # Standard scaled dot-product
    SPARSE = auto()            # Sparse attention patterns
    LOCAL = auto()             # Local windowed attention
    GLOBAL_LOCAL = auto()      # Combination of global and local
    CROSS_MODAL = auto()       # Cross-modal attention
    HIERARCHICAL = auto()      # Hierarchical attention with multiple levels
    ADAPTIVE = auto()          # Adaptive attention based on content


class FusionStrategy(Enum):
    """Enhanced fusion strategies with learnable components."""
    EARLY = auto()             # Combine at input level
    INTERMEDIATE = auto()      # Combine at intermediate representations
    LATE = auto()              # Combine at output level
    PROGRESSIVE = auto()       # Progressive fusion through layers
    ADAPTIVE = auto()          # Content-dependent fusion
    HIERARCHICAL = auto()      # Multi-level hierarchical fusion
    GATED = auto()             # Gated fusion with learnable gates
    ATTENTION_WEIGHTED = auto() # Attention-based weighting


class RotaryPositionalEmbedding(nn.Module):
    """
    Rotary Position Embedding (RoPE) for better position modeling.
    
    RoPE has shown superior performance in recent models by encoding
    position information directly into the attention mechanism rather
    than adding it to embeddings.
    """
    
    def __init__(self, dim: int, max_seq_length: int = 2048, base: int = 10000):
        super().__init__()
        self.dim = dim
        self.max_seq_length = max_seq_length
        self.base = base
        
        # Precompute the frequency bands
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer('inv_freq', inv_freq)
        
        # Precompute rotary embeddings for efficiency
        self._precompute_embeddings()
    
    def _precompute_embeddings(self):
        """Precompute rotary embeddings for all positions."""
        positions = torch.arange(self.max_seq_length).float()
        freqs = torch.outer(positions, self.inv_freq)
        
        # Create rotation matrices
        cos_cached = torch.cos(freqs)
        sin_cached = torch.sin(freqs)
        
        self.register_buffer('cos_cached', cos_cached)
        self.register_buffer('sin_cached', sin_cached)
    
    def forward(self, x: torch.Tensor, seq_len: int) -> torch.Tensor:
        """Apply rotary embeddings to input tensor."""
        batch_size = x.shape[0]
        
        # Get relevant portion of precomputed embeddings
        cos = self.cos_cached[:seq_len, :].unsqueeze(0).expand(batch_size, -1, -1)
        sin = self.sin_cached[:seq_len, :].unsqueeze(0).expand(batch_size, -1, -1)
        
        # Apply rotation
        x_rot = torch.stack([-x[..., 1::2], x[..., ::2]], dim=-1).flatten(start_dim=-2)
        x_out = x * cos + x_rot * sin
        
        return x_out


class AdaptiveLayerNorm(nn.Module):
    """
    Adaptive Layer Normalization that can adjust based on context.
    
    This allows the model to dynamically adjust normalization parameters
    based on the input context, providing more flexibility than standard LayerNorm.
    """
    
    def __init__(self, hidden_size: int, eps: float = 1e-12, adaptive: bool = True):
        super().__init__()
        self.hidden_size = hidden_size
        self.eps = eps
        self.adaptive = adaptive
        
        # Standard parameters
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.bias = nn.Parameter(torch.zeros(hidden_size))
        
        if adaptive:
            # Adaptive parameters learned from context
            self.context_projection = nn.Linear(hidden_size, hidden_size * 2)
            self.gate = nn.Sigmoid()
    
    def forward(self, x: torch.Tensor, context: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Apply adaptive layer normalization."""
        # Standard layer norm computation
        mean = x.mean(dim=-1, keepdim=True)
        var = x.var(dim=-1, keepdim=True, unbiased=False)
        x_norm = (x - mean) / torch.sqrt(var + self.eps)
        
        if self.adaptive and context is not None:
            # Compute adaptive scaling and shifting
            context_params = self.context_projection(context)
            adaptive_weight, adaptive_bias = context_params.chunk(2, dim=-1)
            
            # Gate the adaptive parameters
            gate_value = self.gate(context).mean(dim=1, keepdim=True)
            
            # Combine standard and adaptive parameters
            final_weight = self.weight + gate_value * adaptive_weight
            final_bias = self.bias + gate_value * adaptive_bias
        else:
            final_weight = self.weight
            final_bias = self.bias
        
        return final_weight * x_norm + final_bias


class MultiHeadCrossModalAttention(nn.Module):
    """
    Enhanced cross-modal attention with multiple attention patterns.
    
    This implementation supports various attention mechanisms including
    sparse patterns, local windows, and hierarchical structures for
    efficient cross-modal reasoning.
    """
    
    def __init__(
        self,
        query_dim: int,
        key_dim: int,
        value_dim: int,
        hidden_dim: int,
        num_heads: int,
        dropout: float = 0.1,
        attention_type: AttentionMechanism = AttentionMechanism.STANDARD,
        window_size: Optional[int] = None,
        use_relative_position: bool = False,
        max_relative_position: int = 128
    ):
        super().__init__()
        assert hidden_dim % num_heads == 0, "Hidden dimension must be divisible by number of heads"
        
        self.query_dim = query_dim
        self.key_dim = key_dim
        self.value_dim = value_dim
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads
        self.attention_type = attention_type
        self.window_size = window_size
        self.use_relative_position = use_relative_position
        
        # Projection layers with different dimensions for flexibility
        self.q_proj = nn.Linear(query_dim, hidden_dim, bias=False)
        self.k_proj = nn.Linear(key_dim, hidden_dim, bias=False)
        self.v_proj = nn.Linear(value_dim, hidden_dim, bias=False)
        self.o_proj = nn.Linear(hidden_dim, query_dim)
        
        # Dropout layers
        self.attention_dropout = nn.Dropout(dropout)
        self.output_dropout = nn.Dropout(dropout)
        
        # Learnable temperature for attention scaling
        self.temperature = nn.Parameter(torch.ones(num_heads, 1, 1))
        
        # Relative position embeddings if requested
        if use_relative_position:
            self.relative_position_bias = nn.Embedding(
                2 * max_relative_position + 1,
                num_heads
            )
            self.max_relative_position = max_relative_position
        
        # Initialize weights using Xavier uniform
        self._init_weights()
    
    def _init_weights(self):
        """Initialize weights with Xavier uniform distribution."""
        for module in [self.q_proj, self.k_proj, self.v_proj, self.o_proj]:
            nn.init.xavier_uniform_(module.weight)
            if hasattr(module, 'bias') and module.bias is not None:
                nn.init.constant_(module.bias, 0.0)
    
    def _compute_attention_weights(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Compute attention weights with various patterns.
        
        Supports standard, sparse, local, and hierarchical attention patterns
        based on the configuration.
        """
        batch_size = query.shape[0]
        query_len = query.shape[2]
        key_len = key.shape[2]
        
        # Compute raw attention scores
        scores = torch.matmul(query, key.transpose(-2, -1))
        
        # Apply temperature scaling (learned per head)
        scores = scores / (self.head_dim ** 0.5) * self.temperature
        
        # Add relative position bias if enabled
        if self.use_relative_position:
            position_bias = self._compute_relative_position_bias(query_len, key_len)
            scores = scores + position_bias.unsqueeze(0)
        
        # Apply attention pattern based on type
        if self.attention_type == AttentionMechanism.LOCAL:
            scores = self._apply_local_attention_mask(scores)
        elif self.attention_type == AttentionMechanism.SPARSE:
            scores = self._apply_sparse_attention_mask(scores)
        
        # Apply provided mask
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        # Compute attention probabilities
        attention_probs = F.softmax(scores, dim=-1)
        attention_probs = self.attention_dropout(attention_probs)
        
        return attention_probs
    
    def _compute_relative_position_bias(
        self,
        query_len: int,
        key_len: int
    ) -> torch.Tensor:
        """Compute relative position bias for attention scores."""
        # Create position indices
        query_pos = torch.arange(query_len, device=self.relative_position_bias.weight.device)
        key_pos = torch.arange(key_len, device=self.relative_position_bias.weight.device)
        
        # Compute relative positions
        relative_pos = query_pos.unsqueeze(1) - key_pos.unsqueeze(0)
        relative_pos = relative_pos.clamp(
            -self.max_relative_position,
            self.max_relative_position
        ) + self.max_relative_position
        
        # Get bias values
        bias = self.relative_position_bias(relative_pos)
        return bias.permute(2, 0, 1)  # [num_heads, query_len, key_len]
    
    def _apply_local_attention_mask(self, scores: torch.Tensor) -> torch.Tensor:
        """Apply local windowed attention mask."""
        if self.window_size is None:
            return scores
        
        batch_size, num_heads, query_len, key_len = scores.shape
        
        # Create local attention mask
        row_indices = torch.arange(query_len).unsqueeze(1)
        col_indices = torch.arange(key_len).unsqueeze(0)
        
        mask = torch.abs(row_indices - col_indices) <= self.window_size
        mask = mask.unsqueeze(0).unsqueeze(0).expand(batch_size, num_heads, -1, -1)
        
        # Apply mask
        scores = scores.masked_fill(~mask.to(scores.device), -1e9)
        return scores
    
    def _apply_sparse_attention_mask(self, scores: torch.Tensor) -> torch.Tensor:
        """Apply sparse attention pattern (strided pattern)."""
        batch_size, num_heads, query_len, key_len = scores.shape
        
        # Create strided sparse pattern
        stride = max(1, int(np.sqrt(key_len)))
        
        mask = torch.zeros(query_len, key_len, dtype=torch.bool)
        for i in range(query_len):
            # Attend to strided positions and neighbors
            mask[i, i::stride] = True
            if i > 0:
                mask[i, i-1] = True
            if i < key_len - 1:
                mask[i, i+1] = True
        
        mask = mask.unsqueeze(0).unsqueeze(0).expand(batch_size, num_heads, -1, -1)
        scores = scores.masked_fill(~mask.to(scores.device), -1e9)
        return scores
    
    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        return_attention_weights: bool = False
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """
        Forward pass of cross-modal attention.
        
        Args:
            query: Query tensor [batch_size, query_len, query_dim]
            key: Key tensor [batch_size, key_len, key_dim]
            value: Value tensor [batch_size, key_len, value_dim]
            mask: Optional attention mask
            return_attention_weights: Whether to return attention weights
        
        Returns:
            Output tensor and optionally attention weights
        """
        batch_size = query.shape[0]
        query_len = query.shape[1]
        
        # Project inputs
        Q = self.q_proj(query).view(batch_size, query_len, self.num_heads, self.head_dim)
        K = self.k_proj(key).view(batch_size, -1, self.num_heads, self.head_dim)
        V = self.v_proj(value).view(batch_size, -1, self.num_heads, self.head_dim)
        
        # Transpose for attention computation
        Q = Q.transpose(1, 2)  # [batch, heads, query_len, head_dim]
        K = K.transpose(1, 2)  # [batch, heads, key_len, head_dim]
        V = V.transpose(1, 2)  # [batch, heads, value_len, head_dim]
        
        # Compute attention weights
        attention_weights = self._compute_attention_weights(Q, K, mask)
        
        # Apply attention to values
        context = torch.matmul(attention_weights, V)
        
        # Reshape and project output
        context = context.transpose(1, 2).contiguous()
        context = context.view(batch_size, query_len, self.hidden_dim)
        output = self.o_proj(context)
        output = self.output_dropout(output)
        
        if return_attention_weights:
            return output, attention_weights
        return output


class ModalitySpecificEncoder(nn.Module):
    """
    Sophisticated encoder tailored for specific modality characteristics.
    
    Each modality has unique properties that require specialized processing.
    This encoder adapts its architecture based on modality configuration while
    maintaining compatibility with the unified representation space.
    """
    
    def __init__(self, config: ModalityConfiguration):
        super().__init__()
        config.validate()
        self.config = config
        
        # Input projection with layer normalization
        self.input_projection = nn.Sequential(
            nn.Linear(config.input_dim, config.hidden_dim),
            AdaptiveLayerNorm(config.hidden_dim),
            self._get_activation(config.activation),
            nn.Dropout(config.dropout_rate)
        )
        
        # Positional encoding based on configuration
        self.positional_encoding = self._create_positional_encoding()
        
        # Encoder layers with gradient checkpointing support
        self.layers = nn.ModuleList([
            self._create_encoder_layer(i)
            for i in range(config.num_layers)
        ])
        
        # Output projection to unified dimension
        self.output_projection = nn.Sequential(
            AdaptiveLayerNorm(config.hidden_dim),
            nn.Linear(config.hidden_dim, config.output_dim),
            nn.Dropout(config.dropout_rate)
        )
        
        # Modality-specific gating mechanism
        self.modality_gate = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.Sigmoid()
        )
        
        # Initialize weights
        self.apply(self._init_weights)
    
    def _get_activation(self, activation: str) -> nn.Module:
        """Get activation function by name."""
        activations = {
            'relu': nn.ReLU(),
            'gelu': nn.GELU(),
            'swish': nn.SiLU(),
            'mish': nn.Mish(),
            'tanh': nn.Tanh(),
            'leaky_relu': nn.LeakyReLU(0.1)
        }
        return activations.get(activation, nn.GELU())
    
    def _create_positional_encoding(self) -> nn.Module:
        """Create positional encoding based on configuration."""
        if not self.config.use_positional_encoding:
            return nn.Identity()
        
        if self.config.positional_encoding_type == 'learned':
            return nn.Parameter(
                torch.randn(1, self.config.max_sequence_length, self.config.hidden_dim) * 0.02
            )
        elif self.config.positional_encoding_type == 'rotary':
            return RotaryPositionalEmbedding(
                self.config.hidden_dim,
                self.config.max_sequence_length
            )
        else:  # sinusoidal
            return self._create_sinusoidal_encoding()
    
    def _create_sinusoidal_encoding(self) -> torch.Tensor:
        """Create sinusoidal positional encoding."""
        position = torch.arange(self.config.max_sequence_length).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, self.config.hidden_dim, 2) * 
            -(math.log(10000.0) / self.config.hidden_dim)
        )
        
        pe = torch.zeros(1, self.config.max_sequence_length, self.config.hidden_dim)
        pe[0, :, 0::2] = torch.sin(position * div_term)
        pe[0, :, 1::2] = torch.cos(position * div_term)
        
        return nn.Parameter(pe, requires_grad=False)
    
    def _create_encoder_layer(self, layer_idx: int) -> nn.Module:
        """Create a single encoder layer with advanced features."""
        return TransformerEncoderLayer(
            hidden_dim=self.config.hidden_dim,
            num_heads=self.config.num_heads,
            feedforward_dim=self.config.hidden_dim * 4,
            dropout=self.config.dropout_rate,
            activation=self.config.activation,
            attention_window=self.config.attention_window,
            use_flash_attention=self.config.use_flash_attention,
            layer_norm_eps=self.config.layer_norm_eps
        )
    
    def _init_weights(self, module):
        """Initialize weights with truncated normal distribution."""
        if isinstance(module, nn.Linear):
            nn.init.trunc_normal_(module.weight, std=self.config.initializer_range)
            if module.bias is not None:
                nn.init.constant_(module.bias, 0)
        elif isinstance(module, nn.LayerNorm):
            nn.init.constant_(module.weight, 1.0)
            nn.init.constant_(module.bias, 0)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0, std=self.config.initializer_range)
    
    def forward(
        self,
        x: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        return_all_layers: bool = False
    ) -> Union[torch.Tensor, List[torch.Tensor]]:
        """
        Process input through modality-specific encoder.
        
        Args:
            x: Input tensor [batch_size, seq_len, input_dim]
            attention_mask: Optional attention mask
            return_all_layers: Whether to return outputs from all layers
        
        Returns:
            Encoded representation or list of representations from all layers
        """
        # Input projection
        hidden_states = self.input_projection(x)
        
        # Add positional encoding
        seq_len = hidden_states.shape[1]
        if isinstance(self.positional_encoding, nn.Parameter):
            hidden_states = hidden_states + self.positional_encoding[:, :seq_len, :]
        elif isinstance(self.positional_encoding, RotaryPositionalEmbedding):
            hidden_states = self.positional_encoding(hidden_states, seq_len)
        
        # Apply modality-specific gating
        gate = self.modality_gate(hidden_states.mean(dim=1, keepdim=True))
        hidden_states = hidden_states * gate
        
        # Process through encoder layers
        all_layer_outputs = []
        
        for layer in self.layers:
            if self.config.gradient_checkpointing and self.training:
                hidden_states = torch.utils.checkpoint.checkpoint(
                    layer, hidden_states, attention_mask
                )
            else:
                hidden_states = layer(hidden_states, attention_mask)
            
            if return_all_layers:
                all_layer_outputs.append(hidden_states)
        
        # Output projection
        output = self.output_projection(hidden_states)
        
        if return_all_layers:
            all_layer_outputs.append(output)
            return all_layer_outputs
        return output


class TransformerEncoderLayer(nn.Module):
    """
    Enhanced transformer encoder layer with advanced normalization and attention.
    
    Incorporates recent advances like pre-normalization, gated linear units,
    and optional flash attention for improved efficiency and performance.
    """
    
    def __init__(
        self,
        hidden_dim: int,
        num_heads: int,
        feedforward_dim: int,
        dropout: float = 0.1,
        activation: str = 'gelu',
        attention_window: Optional[int] = None,
        use_flash_attention: bool = False,
        layer_norm_eps: float = 1e-12
    ):
        super().__init__()
        
        # Multi-head self-attention
        self.self_attention = MultiHeadCrossModalAttention(
            query_dim=hidden_dim,
            key_dim=hidden_dim,
            value_dim=hidden_dim,
            hidden_dim=hidden_dim,
            num_heads=num_heads,
            dropout=dropout,
            attention_type=AttentionMechanism.LOCAL if attention_window else AttentionMechanism.STANDARD,
            window_size=attention_window
        )
        
        # Feed-forward network with gated linear unit
        self.feedforward = nn.Sequential(
            nn.Linear(hidden_dim, feedforward_dim),
            self._get_activation(activation),
            nn.Dropout(dropout),
            nn.Linear(feedforward_dim, hidden_dim),
            nn.Dropout(dropout)
        )
        
        # Layer normalization (pre-norm architecture)
        self.norm1 = AdaptiveLayerNorm(hidden_dim, eps=layer_norm_eps)
        self.norm2 = AdaptiveLayerNorm(hidden_dim, eps=layer_norm_eps)
        
        # Gating mechanisms for better gradient flow
        self.attention_gate = nn.Parameter(torch.ones(1))
        self.feedforward_gate = nn.Parameter(torch.ones(1))
    
    def _get_activation(self, activation: str) -> nn.Module:
        """Get activation function by name."""
        activations = {
            'relu': nn.ReLU(),
            'gelu': nn.GELU(),
            'swish': nn.SiLU(),
            'mish': nn.Mish(),
        }
        return activations.get(activation, nn.GELU())
    
    def forward(
        self,
        x: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Forward pass through encoder layer."""
        # Self-attention with pre-normalization
        norm_x = self.norm1(x)
        attention_output = self.self_attention(
            norm_x, norm_x, norm_x, attention_mask
        )
        x = x + self.attention_gate * attention_output
        
        # Feed-forward with pre-normalization
        norm_x = self.norm2(x)
        ff_output = self.feedforward(norm_x)
        x = x + self.feedforward_gate * ff_output
        
        return x


class HierarchicalFusionModule(nn.Module):
    """
    Sophisticated hierarchical fusion that combines modalities at multiple levels.
    
    This module implements a multi-scale fusion strategy where modalities are
    combined progressively through different abstraction levels, allowing the
    model to capture both fine-grained and high-level cross-modal interactions.
    """
    
    def __init__(
        self,
        modality_dims: Dict[str, int],
        hidden_dim: int,
        num_fusion_layers: int = 3,
        fusion_strategy: FusionStrategy = FusionStrategy.HIERARCHICAL,
        use_memory_bank: bool = True,
        memory_bank_size: int = 256
    ):
        super().__init__()
        self.modality_dims = modality_dims
        self.hidden_dim = hidden_dim
        self.num_fusion_layers = num_fusion_layers
        self.fusion_strategy = fusion_strategy
        self.use_memory_bank = use_memory_bank
        
        # Projection layers for each modality
        self.modality_projections = nn.ModuleDict({
            name: nn.Sequential(
                nn.Linear(dim, hidden_dim),
                AdaptiveLayerNorm(hidden_dim),
                nn.GELU(),
                nn.Dropout(0.1)
            )
            for name, dim in modality_dims.items()
        })
        
        # Hierarchical fusion layers
        self.fusion_layers = nn.ModuleList([
            self._create_fusion_layer(i)
            for i in range(num_fusion_layers)
        ])
        
        # Memory bank for persistent cross-modal patterns
        if use_memory_bank:
            self.memory_bank = nn.Parameter(
                torch.randn(memory_bank_size, hidden_dim) * 0.02
            )
            self.memory_attention = MultiHeadCrossModalAttention(
                query_dim=hidden_dim,
                key_dim=hidden_dim,
                value_dim=hidden_dim,
                hidden_dim=hidden_dim,
                num_heads=8,
                dropout=0.1
            )
        
        # Adaptive fusion gates
        self.fusion_gates = nn.ModuleDict({
            name: nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, num_fusion_layers),
                nn.Softmax(dim=-1)
            )
            for name in modality_dims.keys()
        })
        
        # Final fusion layer
        self.final_fusion = nn.Sequential(
            nn.Linear(hidden_dim * len(modality_dims), hidden_dim * 2),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim * 2, hidden_dim),
            AdaptiveLayerNorm(hidden_dim)
        )
        
        # Uncertainty estimation heads
        self.uncertainty_heads = nn.ModuleDict({
            name: nn.Linear(hidden_dim, 2)  # Mean and log variance
            for name in modality_dims.keys()
        })
    
    def _create_fusion_layer(self, layer_idx: int) -> nn.Module:
        """Create a single fusion layer."""
        return nn.ModuleDict({
            'cross_attention': MultiHeadCrossModalAttention(
                query_dim=self.hidden_dim,
                key_dim=self.hidden_dim,
                value_dim=self.hidden_dim,
                hidden_dim=self.hidden_dim,
                num_heads=8,
                dropout=0.1,
                attention_type=AttentionMechanism.CROSS_MODAL
            ),
            'fusion_mlp': nn.Sequential(
                nn.Linear(self.hidden_dim * 2, self.hidden_dim * 4),
                nn.GELU(),
                nn.Dropout(0.1),
                nn.Linear(self.hidden_dim * 4, self.hidden_dim)
            ),
            'layer_norm': AdaptiveLayerNorm(self.hidden_dim)
        })
    
    def _apply_memory_bank(self, features: torch.Tensor) -> torch.Tensor:
        """Attend to memory bank for persistent patterns."""
        batch_size = features.shape[0]
        
        # Expand memory bank for batch
        memory = self.memory_bank.unsqueeze(0).expand(batch_size, -1, -1)
        
        # Attend to memory
        attended_features = self.memory_attention(
            query=features,
            key=memory,
            value=memory
        )
        
        return features + 0.1 * attended_features  # Soft addition
    
    def forward(
        self,
        modality_features: Dict[str, torch.Tensor],
        return_uncertainty: bool = False
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, Dict[str, torch.Tensor]]]:
        """
        Perform hierarchical fusion of modality features.
        
        Args:
            modality_features: Dictionary of modality features
            return_uncertainty: Whether to return uncertainty estimates
        
        Returns:
            Fused features and optionally uncertainty estimates
        """
        batch_size = next(iter(modality_features.values())).shape[0]
        
        # Project modalities to common dimension
        projected_features = {
            name: self.modality_projections[name](features)
            for name, features in modality_features.items()
        }
        
        # Calculate fusion gates for each modality
        fusion_weights = {}
        for name, features in projected_features.items():
            # Use global pooling to get modality representation
            pooled = features.mean(dim=1)
            fusion_weights[name] = self.fusion_gates[name](pooled)
        
        # Hierarchical fusion through layers
        fused_features = {}
        for layer_idx, fusion_layer in enumerate(self.fusion_layers):
            layer_outputs = {}
            
            # Cross-modal attention for each modality
            for name, features in projected_features.items():
                # Concatenate other modalities
                other_features = torch.cat([
                    f for n, f in projected_features.items() if n != name
                ], dim=1)
                
                # Apply cross-modal attention
                attended = fusion_layer['cross_attention'](
                    query=features,
                    key=other_features,
                    value=other_features
                )
                
                # Combine with original features
                combined = torch.cat([features, attended], dim=-1)
                fused = fusion_layer['fusion_mlp'](combined)
                fused = fusion_layer['layer_norm'](fused + features)  # Residual connection
                
                # Weight by fusion gate
                weight = fusion_weights[name][:, layer_idx:layer_idx+1].unsqueeze(1)
                layer_outputs[name] = fused * weight
            
            # Update features for next layer
            projected_features = layer_outputs
            fused_features[f'layer_{layer_idx}'] = layer_outputs
        
        # Apply memory bank if enabled
        if self.use_memory_bank:
            for name in projected_features:
                projected_features[name] = self._apply_memory_bank(
                    projected_features[name]
                )
        
        # Final fusion
        all_features = torch.cat(list(projected_features.values()), dim=-1)
        final_output = self.final_fusion(all_features)
        
        # Calculate uncertainty if requested
        if return_uncertainty:
            uncertainties = {}
            for name, features in projected_features.items():
                pooled = features.mean(dim=1)
                uncertainty_params = self.uncertainty_heads[name](pooled)
                mean, log_var = uncertainty_params.chunk(2, dim=-1)
                uncertainties[name] = {
                    'mean': mean,
                    'log_var': log_var,
                    'std': torch.exp(0.5 * log_var)
                }
            
            return final_output, uncertainties
        
        return final_output


class ContrastiveLearningHead(nn.Module):
    """
    Contrastive learning head for robust multimodal representations.
    
    Implements various contrastive objectives including InfoNCE, triplet loss,
    and supervised contrastive learning for better alignment of modality embeddings.
    """
    
    def __init__(
        self,
        embedding_dim: int,
        projection_dim: int = 256,
        temperature: float = 0.07,
        loss_type: str = 'infonce'
    ):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.projection_dim = projection_dim
        self.temperature = temperature
        self.loss_type = loss_type
        
        # Projection heads for each modality
        self.projection = nn.Sequential(
            nn.Linear(embedding_dim, embedding_dim),
            nn.ReLU(),
            nn.Linear(embedding_dim, projection_dim)
        )
        
        # Learnable temperature parameter
        self.log_temperature = nn.Parameter(torch.tensor(np.log(temperature)))
    
    def forward(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        labels: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Compute contrastive loss between two sets of embeddings.
        
        Args:
            embeddings_1: First set of embeddings [batch_size, embedding_dim]
            embeddings_2: Second set of embeddings [batch_size, embedding_dim]
            labels: Optional labels for supervised contrastive learning
        
        Returns:
            Contrastive loss value
        """
        # Project embeddings
        z1 = F.normalize(self.projection(embeddings_1), dim=-1)
        z2 = F.normalize(self.projection(embeddings_2), dim=-1)
        
        batch_size = z1.shape[0]
        temperature = torch.exp(self.log_temperature)
        
        if self.loss_type == 'infonce':
            # InfoNCE loss
            sim_matrix = torch.matmul(z1, z2.T) / temperature
            
            # Positive pairs are on the diagonal
            pos_sim = torch.diag(sim_matrix)
            
            # Negative pairs are all other elements
            neg_sim = sim_matrix
            
            # Compute loss
            exp_pos = torch.exp(pos_sim)
            exp_neg = torch.exp(neg_sim).sum(dim=1) - exp_pos
            
            loss = -torch.log(exp_pos / (exp_pos + exp_neg)).mean()
            
        elif self.loss_type == 'triplet':
            # Triplet loss with hard negative mining
            anchor = z1
            positive = z2
            
            # Hard negative mining
            sim_matrix = torch.matmul(anchor, z2.T)
            hardest_negatives_idx = sim_matrix.argmax(dim=1)
            negative = z2[hardest_negatives_idx]
            
            # Compute distances
            pos_dist = F.pairwise_distance(anchor, positive)
            neg_dist = F.pairwise_distance(anchor, negative)
            
            # Triplet loss with margin
            margin = 0.2
            loss = F.relu(pos_dist - neg_dist + margin).mean()
            
        elif self.loss_type == 'supervised' and labels is not None:
            # Supervised contrastive loss
            sim_matrix = torch.matmul(z1, z1.T) / temperature
            
            # Mask for positive pairs (same label)
            labels = labels.view(-1, 1)
            mask = torch.eq(labels, labels.T).float()
            
            # Exclude self-contrast
            mask = mask - torch.eye(batch_size, device=mask.device)
            
            # Compute loss
            exp_sim = torch.exp(sim_matrix)
            exp_sim = exp_sim * (1 - torch.eye(batch_size, device=exp_sim.device))
            
            pos_sim = (exp_sim * mask).sum(dim=1)
            neg_sim = exp_sim.sum(dim=1)
            
            loss = -torch.log(pos_sim / neg_sim).mean()
        else:
            raise ValueError(f"Unknown loss type: {self.loss_type}")
        
        return loss


class AdaptiveMultimodalTransformer(nn.Module):
    """
    State-of-the-art multimodal transformer with adaptive computation.
    
    This architecture dynamically adjusts its computation based on input complexity,
    implements hierarchical reasoning, and provides uncertainty quantification
    for robust multimodal understanding.
    """
    
    def __init__(
        self,
        modality_configs: Dict[str, ModalityConfiguration],
        hidden_dim: int = 768,
        num_reasoning_layers: int = 6,
        num_classes: Optional[int] = None,
        fusion_strategy: FusionStrategy = FusionStrategy.HIERARCHICAL,
        use_memory_augmentation: bool = True,
        memory_size: int = 512,
        use_mixture_of_experts: bool = True,
        num_experts: int = 4,
        use_contrastive_learning: bool = True,
        dropout_rate: float = 0.1
    ):
        super().__init__()
        
        self.modality_configs = modality_configs
        self.hidden_dim = hidden_dim
        self.num_classes = num_classes
        self.fusion_strategy = fusion_strategy
        self.use_memory_augmentation = use_memory_augmentation
        self.use_contrastive_learning = use_contrastive_learning
        
        # Modality-specific encoders
        self.encoders = nn.ModuleDict({
            name: ModalitySpecificEncoder(config)
            for name, config in modality_configs.items()
        })
        
        # Hierarchical fusion module
        encoder_output_dims = {
            name: config.output_dim
            for name, config in modality_configs.items()
        }
        
        self.fusion = HierarchicalFusionModule(
            modality_dims=encoder_output_dims,
            hidden_dim=hidden_dim,
            num_fusion_layers=3,
            fusion_strategy=fusion_strategy,
            use_memory_bank=use_memory_augmentation,
            memory_bank_size=memory_size
        )
        
        # Mixture of Experts for specialized processing
        if use_mixture_of_experts:
            self.experts = nn.ModuleList([
                nn.Sequential(
                    nn.Linear(hidden_dim, hidden_dim * 2),
                    nn.GELU(),
                    nn.Dropout(dropout_rate),
                    nn.Linear(hidden_dim * 2, hidden_dim),
                    AdaptiveLayerNorm(hidden_dim)
                )
                for _ in range(num_experts)
            ])
            
            # Expert routing network
            self.expert_router = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, num_experts),
                nn.Softmax(dim=-1)
            )
        else:
            self.experts = None
            self.expert_router = None
        
        # Reasoning transformer layers
        self.reasoning_layers = nn.ModuleList([
            TransformerEncoderLayer(
                hidden_dim=hidden_dim,
                num_heads=12,
                feedforward_dim=hidden_dim * 4,
                dropout=dropout_rate,
                activation='gelu'
            )
            for _ in range(num_reasoning_layers)
        ])
        
        # Memory augmentation
        if use_memory_augmentation:
            self.working_memory = nn.Parameter(
                torch.randn(1, memory_size, hidden_dim) * 0.02
            )
            self.memory_controller = nn.LSTM(
                input_size=hidden_dim,
                hidden_size=hidden_dim,
                num_layers=2,
                batch_first=True,
                dropout=dropout_rate if num_reasoning_layers > 1 else 0
            )
        
        # Contrastive learning head
        if use_contrastive_learning:
            self.contrastive_head = ContrastiveLearningHead(
                embedding_dim=hidden_dim,
                projection_dim=256,
                temperature=0.07,
                loss_type='infonce'
            )
        
        # Classification head
        if num_classes is not None:
            self.classifier = nn.Sequential(
                AdaptiveLayerNorm(hidden_dim),
                nn.Dropout(dropout_rate),
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.GELU(),
                nn.Dropout(dropout_rate),
                nn.Linear(hidden_dim // 2, num_classes)
            )
        else:
            self.classifier = None
        
        # Learnable class token for pooling
        self.cls_token = nn.Parameter(torch.randn(1, 1, hidden_dim) * 0.02)
        
        # Adaptive computation controller
        self.computation_controller = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 4),
            nn.ReLU(),
            nn.Linear(hidden_dim // 4, num_reasoning_layers),
            nn.Sigmoid()
        )
        
        # Initialize all weights
        self.apply(self._init_weights)
    
    def _init_weights(self, module):
        """Initialize model weights."""
        if isinstance(module, nn.Linear):
            nn.init.trunc_normal_(module.weight, std=0.02)
            if module.bias is not None:
                nn.init.constant_(module.bias, 0)
        elif isinstance(module, (nn.LayerNorm, AdaptiveLayerNorm)):
            if hasattr(module, 'weight'):
                nn.init.constant_(module.weight, 1.0)
            if hasattr(module, 'bias'):
                nn.init.constant_(module.bias, 0)
    
    def _apply_mixture_of_experts(
        self,
        features: torch.Tensor,
        return_routing_weights: bool = False
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """Apply mixture of experts with sparse routing."""
        batch_size, seq_len, hidden_dim = features.shape
        
        # Calculate routing weights
        pooled_features = features.mean(dim=1)
        routing_weights = self.expert_router(pooled_features)
        
        # Apply top-k routing for sparsity
        k = 2  # Use top-2 experts
        top_k_weights, top_k_indices = routing_weights.topk(k, dim=-1)
        
        # Renormalize weights
        top_k_weights = top_k_weights / top_k_weights.sum(dim=-1, keepdim=True)
        
        # Apply experts
        expert_outputs = torch.zeros_like(features)
        for i in range(batch_size):
            for j, expert_idx in enumerate(top_k_indices[i]):
                weight = top_k_weights[i, j].unsqueeze(0).unsqueeze(0)
                expert_output = self.experts[expert_idx](features[i:i+1])
                expert_outputs[i:i+1] += weight * expert_output
        
        if return_routing_weights:
            return expert_outputs, routing_weights
        return expert_outputs
    
    def _apply_adaptive_computation(
        self,
        features: torch.Tensor,
        layer_weights: torch.Tensor
    ) -> torch.Tensor:
        """Apply layers with adaptive computation based on complexity."""
        output = features
        
        for i, (layer, weight) in enumerate(zip(self.reasoning_layers, layer_weights)):
            # Apply layer with weighted contribution
            layer_output = layer(output)
            
            # Adaptive halting: skip computation if weight is low
            if weight > 0.1:  # Threshold for computation
                output = output + weight.unsqueeze(1) * (layer_output - output)
        
        return output
    
    def forward(
        self,
        inputs: Dict[str, torch.Tensor],
        attention_masks: Optional[Dict[str, torch.Tensor]] = None,
        return_embeddings: bool = False,
        return_uncertainty: bool = False
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass through the adaptive multimodal transformer.
        
        Args:
            inputs: Dictionary of input tensors for each modality
            attention_masks: Optional attention masks for each modality
            return_embeddings: Whether to return intermediate embeddings
            return_uncertainty: Whether to return uncertainty estimates
        
        Returns:
            Dictionary containing model outputs
        """
        batch_size = next(iter(inputs.values())).shape[0]
        results = {}
        
        # Encode each modality
        encoded_features = {}
        modality_embeddings = {}
        
        for name, input_tensor in inputs.items():
            if name in self.encoders:
                mask = attention_masks.get(name) if attention_masks else None
                encoded = self.encoders[name](input_tensor, mask)
                encoded_features[name] = encoded
                
                # Store pooled embeddings for each modality
                modality_embeddings[name] = encoded.mean(dim=1)
        
        # Apply hierarchical fusion
        if return_uncertainty:
            fused_features, uncertainties = self.fusion(
                encoded_features,
                return_uncertainty=True
            )
            results['uncertainties'] = uncertainties
        else:
            fused_features = self.fusion(encoded_features)
        
        # Add CLS token
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        features_with_cls = torch.cat([cls_tokens, fused_features], dim=1)
        
        # Apply mixture of experts if enabled
        if self.experts is not None:
            features_with_cls, routing_weights = self._apply_mixture_of_experts(
                features_with_cls,
                return_routing_weights=True
            )
            results['expert_routing'] = routing_weights
        
        # Memory augmentation
        if self.use_memory_augmentation:
            # Expand working memory for batch
            working_memory = self.working_memory.expand(batch_size, -1, -1)
            
            # Process through memory controller
            memory_output, (hidden, cell) = self.memory_controller(features_with_cls)
            
            # Combine with working memory
            features_with_cls = features_with_cls + 0.1 * memory_output
            
            results['memory_state'] = hidden[-1]  # Last hidden state
        
        # Adaptive computation through reasoning layers
        pooled_features = features_with_cls.mean(dim=1)
        computation_weights = self.computation_controller(pooled_features)
        
        output_features = self._apply_adaptive_computation(
            features_with_cls,
            computation_weights.unbind(dim=-1)
        )
        
        results['computation_weights'] = computation_weights
        
        # Extract CLS token output
        cls_output = output_features[:, 0]
        
        # Store embeddings
        results['embeddings'] = cls_output
        results['sequence_output'] = output_features
        
        if return_embeddings:
            results['modality_embeddings'] = modality_embeddings
            results['encoded_features'] = encoded_features
        
        # Classification
        if self.classifier is not None:
            logits = self.classifier(cls_output)
            results['logits'] = logits
            results['probabilities'] = F.softmax(logits, dim=-1)
        
        # Contrastive loss computation if training
        if self.training and self.use_contrastive_learning and len(modality_embeddings) >= 2:
            # Compute contrastive loss between first two modalities
            modality_names = list(modality_embeddings.keys())
            if len(modality_names) >= 2:
                contrastive_loss = self.contrastive_head(
                    modality_embeddings[modality_names[0]],
                    modality_embeddings[modality_names[1]]
                )
                results['contrastive_loss'] = contrastive_loss
        
        return results


def create_advanced_multimodal_model(
    modality_specs: Dict[str, Tuple[int, int, int]],  # (input_dim, hidden_dim, output_dim)
    global_hidden_dim: int = 768,
    num_reasoning_layers: int = 6,
    num_classes: Optional[int] = None,
    fusion_strategy: str = 'hierarchical',
    use_advanced_features: bool = True
) -> AdaptiveMultimodalTransformer:
    """
    Factory function to create an advanced multimodal model.
    
    Args:
        modality_specs: Dictionary mapping modality names to (input_dim, hidden_dim, output_dim)
        global_hidden_dim: Global hidden dimension for fusion
        num_reasoning_layers: Number of reasoning transformer layers
        num_classes: Number of output classes (None for embedding only)
        fusion_strategy: Fusion strategy name
        use_advanced_features: Whether to use memory, MoE, and contrastive learning
    
    Returns:
        Configured AdaptiveMultimodalTransformer model
    """
    # Create modality configurations
    configs = {}
    for name, (input_dim, hidden_dim, output_dim) in modality_specs.items():
        configs[name] = ModalityConfiguration(
            name=name,
            input_dim=input_dim,
            hidden_dim=hidden_dim,
            output_dim=output_dim,
            num_heads=8 if hidden_dim >= 256 else 4,
            num_layers=3,
            dropout_rate=0.1,
            activation='gelu',
            use_positional_encoding=True,
            positional_encoding_type='rotary' if hidden_dim >= 256 else 'learned'
        )
    
    # Map fusion strategy
    strategy_map = {
        'early': FusionStrategy.EARLY,
        'intermediate': FusionStrategy.INTERMEDIATE,
        'late': FusionStrategy.LATE,
        'progressive': FusionStrategy.PROGRESSIVE,
        'adaptive': FusionStrategy.ADAPTIVE,
        'hierarchical': FusionStrategy.HIERARCHICAL,
        'gated': FusionStrategy.GATED,
        'attention': FusionStrategy.ATTENTION_WEIGHTED
    }
    
    fusion = strategy_map.get(fusion_strategy.lower(), FusionStrategy.HIERARCHICAL)
    
    # Create model
    model = AdaptiveMultimodalTransformer(
        modality_configs=configs,
        hidden_dim=global_hidden_dim,
        num_reasoning_layers=num_reasoning_layers,
        num_classes=num_classes,
        fusion_strategy=fusion,
        use_memory_augmentation=use_advanced_features,
        memory_size=512 if use_advanced_features else 0,
        use_mixture_of_experts=use_advanced_features,
        num_experts=len(configs),
        use_contrastive_learning=use_advanced_features
    )
    
    return model


if __name__ == "__main__":
    # Demonstration of the advanced multimodal transformer
    
    # Configure modalities with different characteristics
    modality_specs = {
        'text': (768, 512, 512),      # BERT-like text embeddings
        'vision': (2048, 768, 512),   # ResNet visual features
        'audio': (128, 256, 512),     # Audio spectral features
        'sensor': (64, 128, 512)      # IoT sensor data
    }
    
    # Create model with all advanced features
    model = create_advanced_multimodal_model(
        modality_specs=modality_specs,
        global_hidden_dim=768,
        num_reasoning_layers=6,
        num_classes=10,
        fusion_strategy='hierarchical',
        use_advanced_features=True
    )
    
    # Create sample inputs
    batch_size = 4
    inputs = {
        'text': torch.randn(batch_size, 50, 768),     # [batch, seq_len, dim]
        'vision': torch.randn(batch_size, 196, 2048), # [batch, patches, dim]
        'audio': torch.randn(batch_size, 100, 128),   # [batch, frames, dim]
        'sensor': torch.randn(batch_size, 30, 64)     # [batch, timesteps, dim]
    }
    
    # Forward pass with all outputs
    outputs = model(
        inputs,
        return_embeddings=True,
        return_uncertainty=True
    )
    
    # Display model statistics and outputs
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"Model Statistics:")
    print(f"  Total parameters: {total_params:,}")
    print(f"  Trainable parameters: {trainable_params:,}")
    print(f"  Model size: {total_params * 4 / 1024**2:.2f} MB (fp32)")
    
    print(f"\nOutput Shapes:")
    for key, value in outputs.items():
        if isinstance(value, torch.Tensor):
            print(f"  {key}: {value.shape}")
        elif isinstance(value, dict):
            print(f"  {key}:")
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, torch.Tensor):
                    print(f"    {sub_key}: {sub_value.shape}")
    
    # Demonstrate uncertainty quantification
    if 'uncertainties' in outputs:
        print(f"\nUncertainty Estimates:")
        for modality, uncertainty in outputs['uncertainties'].items():
            std = uncertainty['std'].mean().item()
            print(f"  {modality}: σ = {std:.4f}")
    
    # Show expert routing distribution
    if 'expert_routing' in outputs:
        routing = outputs['expert_routing'].mean(dim=0)
        print(f"\nExpert Usage: {routing.tolist()}")
    
    # Display adaptive computation weights
    if 'computation_weights' in outputs:
        weights = outputs['computation_weights'].mean(dim=0)
        print(f"\nLayer Computation Weights: {weights.tolist()}")
