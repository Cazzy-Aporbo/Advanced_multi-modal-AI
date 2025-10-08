"""
Advanced Attention Mechanisms for Multimodal AI
Attention mechanisms optimized for multimodal learning
Including efficient variants, cross-modal attention, and memory-augmented approaches.
Date: 10/7/2025

"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict, List, Union
import math
import numpy as np
from dataclasses import dataclass
from einops import rearrange, repeat


@dataclass
class AttentionConfig:
    """Configuration for attention mechanisms"""
    hidden_dim: int
    num_heads: int
    dropout: float = 0.1
    use_flash_attention: bool = False
    use_rotary_embedding: bool = True
    max_seq_length: int = 8192
    attention_window: int = 256  # For local attention
    use_alibi: bool = False  # Attention with Linear Biases


class RotaryPositionalEmbedding(nn.Module):
    """
    Rotary Position Embedding (RoPE) for better position encoding
    Used in modern LLMs for improved length generalization
    """
    
    def __init__(self, dim: int, max_seq_length: int = 8192, base: int = 10000):
        super().__init__()
        self.dim = dim
        self.max_seq_length = max_seq_length
        self.base = base
        
        # Precompute frequencies
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer('inv_freq', inv_freq)
        
        # Precompute cos and sin
        t = torch.arange(max_seq_length).float()
        freqs = torch.einsum('i,j->ij', t, self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        self.register_buffer('cos_cached', emb.cos())
        self.register_buffer('sin_cached', emb.sin())
    
    def forward(self, q: torch.Tensor, k: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        seq_len = q.shape[1]
        
        # Apply rotary embeddings
        cos = self.cos_cached[:seq_len, :].to(q.dtype)
        sin = self.sin_cached[:seq_len, :].to(q.dtype)
        
        q_embed = (q * cos) + (self.rotate_half(q) * sin)
        k_embed = (k * cos) + (self.rotate_half(k) * sin)
        
        return q_embed, k_embed
    
    def rotate_half(self, x: torch.Tensor) -> torch.Tensor:
        x1, x2 = x.chunk(2, dim=-1)
        return torch.cat((-x2, x1), dim=-1)


class MultiHeadCrossModalAttention(nn.Module):
    """
    Enhanced cross-modal attention with multiple attention patterns
    Supports asymmetric attention and modality-specific processing
    """
    
    def __init__(
        self,
        query_dim: int,
        key_dim: int,
        value_dim: int,
        output_dim: int,
        num_heads: int = 8,
        dropout: float = 0.1,
        use_rope: bool = True
    ):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = output_dim // num_heads
        
        # Asymmetric projections for different modalities
        self.q_proj = nn.Linear(query_dim, output_dim)
        self.k_proj = nn.Linear(key_dim, output_dim)
        self.v_proj = nn.Linear(value_dim, output_dim)
        self.out_proj = nn.Linear(output_dim, output_dim)
        
        # Learnable temperature per head
        self.temperatures = nn.Parameter(torch.ones(num_heads))
        
        # Modality-specific scaling
        self.query_scale = nn.Parameter(torch.ones(1))
        self.key_scale = nn.Parameter(torch.ones(1))
        
        # Rotary embeddings
        if use_rope:
            self.rope = RotaryPositionalEmbedding(self.head_dim)
        else:
            self.rope = None
        
        self.dropout = nn.Dropout(dropout)
        
    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        return_attention: bool = False
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        
        batch_size, query_len, _ = query.shape
        key_len = key.shape[1]
        
        # Project and reshape
        Q = self.q_proj(query) * self.query_scale
        K = self.k_proj(key) * self.key_scale
        V = self.v_proj(value)
        
        Q = rearrange(Q, 'b n (h d) -> b h n d', h=self.num_heads)
        K = rearrange(K, 'b n (h d) -> b h n d', h=self.num_heads)
        V = rearrange(V, 'b n (h d) -> b h n d', h=self.num_heads)
        
        # Apply rotary embeddings if enabled
        if self.rope is not None:
            Q, K = self.rope(Q, K)
        
        # Scaled dot-product attention with per-head temperature
        scores = torch.matmul(Q, K.transpose(-2, -1))
        scores = scores / (self.head_dim ** 0.5)
        scores = scores / self.temperatures.view(1, -1, 1, 1)
        
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # Apply attention
        context = torch.matmul(attn_weights, V)
        context = rearrange(context, 'b h n d -> b n (h d)')
        
        output = self.out_proj(context)
        
        if return_attention:
            return output, attn_weights
        return output


class SparseAttention(nn.Module):
    """
    Sparse attention mechanism for efficient long-sequence processing
    Implements sliding window and dilated attention patterns
    """
    
    def __init__(
        self,
        hidden_dim: int,
        num_heads: int = 8,
        window_size: int = 256,
        dilation_rate: int = 2,
        dropout: float = 0.1
    ):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads
        self.window_size = window_size
        self.dilation_rate = dilation_rate
        
        self.qkv = nn.Linear(hidden_dim, 3 * hidden_dim)
        self.out_proj = nn.Linear(hidden_dim, hidden_dim)
        self.dropout = nn.Dropout(dropout)
        
    def create_sparse_mask(self, seq_len: int, device: torch.device) -> torch.Tensor:
        """Create sparse attention mask with sliding window and dilation"""
        mask = torch.zeros(seq_len, seq_len, device=device)
        
        for i in range(seq_len):
            # Sliding window
            start = max(0, i - self.window_size // 2)
            end = min(seq_len, i + self.window_size // 2 + 1)
            mask[i, start:end] = 1
            
            # Dilated attention
            dilated_indices = torch.arange(
                i % self.dilation_rate, 
                seq_len, 
                self.dilation_rate,
                device=device
            )
            if len(dilated_indices) > 0:
                mask[i, dilated_indices] = 1
        
        return mask
    
    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        batch_size, seq_len, _ = x.shape
        
        # Generate QKV
        qkv = self.qkv(x)
        Q, K, V = rearrange(qkv, 'b n (three h d) -> three b h n d', 
                           three=3, h=self.num_heads)
        
        # Create sparse mask
        sparse_mask = self.create_sparse_mask(seq_len, x.device)
        sparse_mask = sparse_mask.unsqueeze(0).unsqueeze(0)
        
        # Compute attention scores
        scores = torch.matmul(Q, K.transpose(-2, -1)) / (self.head_dim ** 0.5)
        
        # Apply sparse mask
        scores = scores.masked_fill(sparse_mask == 0, -1e9)
        
        # Apply additional mask if provided
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # Apply attention
        context = torch.matmul(attn_weights, V)
        context = rearrange(context, 'b h n d -> b n (h d)')
        
        return self.out_proj(context)


class LocalGlobalAttention(nn.Module):
    """
    Combines local sliding window attention with global attention
    Efficient for long sequences while maintaining global context
    """
    
    def __init__(
        self,
        hidden_dim: int,
        num_heads: int = 8,
        local_window: int = 128,
        num_global_tokens: int = 16,
        dropout: float = 0.1
    ):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads
        self.local_window = local_window
        self.num_global_tokens = num_global_tokens
        
        # Separate projections for local and global attention
        self.local_qkv = nn.Linear(hidden_dim, 3 * hidden_dim)
        self.global_qkv = nn.Linear(hidden_dim, 3 * hidden_dim)
        
        # Global token parameters
        self.global_tokens = nn.Parameter(
            torch.randn(1, num_global_tokens, hidden_dim)
        )
        
        self.out_proj = nn.Linear(hidden_dim, hidden_dim)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len, _ = x.shape
        
        # Expand global tokens for batch
        global_tokens = self.global_tokens.expand(batch_size, -1, -1)
        
        # Local attention
        local_qkv = self.local_qkv(x)
        Q_local, K_local, V_local = rearrange(
            local_qkv, 'b n (three h d) -> three b h n d',
            three=3, h=self.num_heads
        )
        
        # Create local attention mask
        local_mask = self.create_local_mask(seq_len, self.local_window, x.device)
        
        # Compute local attention
        local_scores = torch.matmul(Q_local, K_local.transpose(-2, -1))
        local_scores = local_scores / (self.head_dim ** 0.5)
        local_scores = local_scores.masked_fill(local_mask == 0, -1e9)
        local_attn = F.softmax(local_scores, dim=-1)
        local_context = torch.matmul(local_attn, V_local)
        
        # Global attention
        global_qkv = self.global_qkv(torch.cat([global_tokens, x], dim=1))
        Q_global, K_global, V_global = rearrange(
            global_qkv, 'b n (three h d) -> three b h n d',
            three=3, h=self.num_heads
        )
        
        # All tokens attend to global tokens
        global_scores = torch.matmul(
            Q_global[:, self.num_global_tokens:],
            K_global[:, :self.num_global_tokens].transpose(-2, -1)
        )
        global_scores = global_scores / (self.head_dim ** 0.5)
        global_attn = F.softmax(global_scores, dim=-1)
        global_context = torch.matmul(global_attn, V_global[:, :self.num_global_tokens])
        
        # Combine local and global contexts
        combined = local_context + global_context
        combined = rearrange(combined, 'b h n d -> b n (h d)')
        
        return self.out_proj(combined)
    
    @staticmethod
    def create_local_mask(seq_len: int, window: int, device: torch.device) -> torch.Tensor:
        mask = torch.zeros(seq_len, seq_len, device=device)
        for i in range(seq_len):
            start = max(0, i - window // 2)
            end = min(seq_len, i + window // 2 + 1)
            mask[i, start:end] = 1
        return mask.unsqueeze(0).unsqueeze(0)


class MemoryAugmentedAttention(nn.Module):
    """
    Attention with external memory bank for storing long-term information
    Useful for maintaining context across long sequences or multiple inputs
    """
    
    def __init__(
        self,
        hidden_dim: int,
        memory_size: int = 256,
        memory_dim: int = None,
        num_heads: int = 8,
        dropout: float = 0.1
    ):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.memory_dim = memory_dim or hidden_dim
        self.memory_size = memory_size
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads
        
        # Memory bank
        self.memory_bank = nn.Parameter(
            torch.randn(1, memory_size, self.memory_dim)
        )
        
        # Memory key and value projections
        self.memory_key = nn.Linear(self.memory_dim, hidden_dim)
        self.memory_value = nn.Linear(self.memory_dim, hidden_dim)
        
        # Query projection
        self.q_proj = nn.Linear(hidden_dim, hidden_dim)
        self.k_proj = nn.Linear(hidden_dim, hidden_dim)
        self.v_proj = nn.Linear(hidden_dim, hidden_dim)
        
        # Memory gating
        self.memory_gate = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
        
        self.out_proj = nn.Linear(hidden_dim, hidden_dim)
        self.dropout = nn.Dropout(dropout)
        
    def forward(
        self,
        x: torch.Tensor,
        update_memory: bool = False
    ) -> torch.Tensor:
        batch_size, seq_len, _ = x.shape
        
        # Expand memory for batch
        memory = self.memory_bank.expand(batch_size, -1, -1)
        
        # Project inputs
        Q = rearrange(self.q_proj(x), 'b n (h d) -> b h n d', h=self.num_heads)
        K_input = rearrange(self.k_proj(x), 'b n (h d) -> b h n d', h=self.num_heads)
        V_input = rearrange(self.v_proj(x), 'b n (h d) -> b h n d', h=self.num_heads)
        
        # Project memory
        K_memory = rearrange(
            self.memory_key(memory), 'b m (h d) -> b h m d', h=self.num_heads
        )
        V_memory = rearrange(
            self.memory_value(memory), 'b m (h d) -> b h m d', h=self.num_heads
        )
        
        # Concatenate input and memory keys/values
        K = torch.cat([K_memory, K_input], dim=2)
        V = torch.cat([V_memory, V_input], dim=2)
        
        # Compute attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / (self.head_dim ** 0.5)
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        context = torch.matmul(attn_weights, V)
        context = rearrange(context, 'b h n d -> b n (h d)')
        
        # Apply memory gating
        gate = self.memory_gate(x)
        output = gate * context + (1 - gate) * x
        
        # Update memory if specified
        if update_memory:
            # Use attention weights to update memory
            memory_attn = attn_weights[:, :, :, :self.memory_size].mean(dim=1)
            memory_update = torch.matmul(memory_attn.transpose(-2, -1), x)
            self.memory_bank.data = 0.9 * self.memory_bank.data + 0.1 * memory_update.mean(dim=0, keepdim=True)
        
        return self.out_proj(output)


class ChannelAttention(nn.Module):
    """
    Channel attention mechanism for feature recalibration
    Similar to Squeeze-and-Excitation but adapted for transformers
    """
    
    def __init__(self, channels: int, reduction_ratio: int = 8):
        super().__init__()
        self.avg_pool = nn.AdaptiveAvgPool1d(1)
        self.max_pool = nn.AdaptiveMaxPool1d(1)
        
        self.fc = nn.Sequential(
            nn.Linear(channels, channels // reduction_ratio, bias=False),
            nn.ReLU(),
            nn.Linear(channels // reduction_ratio, channels, bias=False)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len, channels = x.shape
        
        # Transpose for pooling
        x_t = x.transpose(1, 2)  # [batch, channels, seq_len]
        
        # Channel-wise statistics
        avg_out = self.avg_pool(x_t).squeeze(-1)
        max_out = self.max_pool(x_t).squeeze(-1)
        
        # Generate attention weights
        avg_weights = self.fc(avg_out)
        max_weights = self.fc(max_out)
        weights = torch.sigmoid(avg_weights + max_weights).unsqueeze(1)
        
        # Apply channel attention
        return x * weights


class SpatialAttention(nn.Module):
    """
    Spatial attention for focusing on important regions
    Useful for vision and spatial modalities
    """
    
    def __init__(self, kernel_size: int = 7):
        super().__init__()
        self.conv = nn.Conv1d(
            2, 1, 
            kernel_size=kernel_size,
            padding=kernel_size // 2,
            bias=False
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Compute spatial statistics
        avg_out = torch.mean(x, dim=-1, keepdim=True)
        max_out, _ = torch.max(x, dim=-1, keepdim=True)
        
        # Concatenate and convolve
        concat = torch.cat([avg_out, max_out], dim=-1)
        concat = concat.transpose(1, 2)  # [batch, 2, seq_len]
        
        attention = self.conv(concat)
        attention = torch.sigmoid(attention).transpose(1, 2)
        
        return x * attention


class TemporalAttention(nn.Module):
    """
    Temporal attention for sequential data
    Includes causal masking and temporal decay
    """
    
    def __init__(
        self,
        hidden_dim: int,
        num_heads: int = 8,
        use_decay: bool = True,
        dropout: float = 0.1
    ):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads
        self.use_decay = use_decay
        
        self.qkv = nn.Linear(hidden_dim, 3 * hidden_dim)
        self.out_proj = nn.Linear(hidden_dim, hidden_dim)
        
        # Temporal decay parameters
        if use_decay:
            self.decay_weight = nn.Parameter(torch.ones(num_heads))
            self.decay_bias = nn.Parameter(torch.zeros(num_heads))
        
        self.dropout = nn.Dropout(dropout)
        
    def forward(
        self,
        x: torch.Tensor,
        use_causal_mask: bool = True
    ) -> torch.Tensor:
        batch_size, seq_len, _ = x.shape
        
        # Generate QKV
        qkv = self.qkv(x)
        Q, K, V = rearrange(qkv, 'b n (three h d) -> three b h n d',
                           three=3, h=self.num_heads)
        
        # Compute attention scores
        scores = torch.matmul(Q, K.transpose(-2, -1)) / (self.head_dim ** 0.5)
        
        # Apply temporal decay
        if self.use_decay:
            positions = torch.arange(seq_len, device=x.device).unsqueeze(0)
            distances = (positions.unsqueeze(-1) - positions.unsqueeze(-2)).float()
            decay = torch.exp(-F.relu(distances) * self.decay_weight.view(1, -1, 1, 1) 
                             + self.decay_bias.view(1, -1, 1, 1))
            scores = scores * decay
        
        # Apply causal mask if specified
        if use_causal_mask:
            mask = torch.triu(torch.ones(seq_len, seq_len, device=x.device), diagonal=1)
            scores = scores.masked_fill(mask.bool(), -1e9)
        
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # Apply attention
        context = torch.matmul(attn_weights, V)
        context = rearrange(context, 'b h n d -> b n (h d)')
        
        return self.out_proj(context)


class FlashAttention(nn.Module):
    """
    Efficient attention implementation inspired by Flash Attention
    Uses chunking and recomputation for memory efficiency
    Note: This is a simplified version for demonstration
    """
    
    def __init__(
        self,
        hidden_dim: int,
        num_heads: int = 8,
        chunk_size: int = 256,
        dropout: float = 0.1
    ):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads
        self.chunk_size = chunk_size
        
        self.qkv = nn.Linear(hidden_dim, 3 * hidden_dim)
        self.out_proj = nn.Linear(hidden_dim, hidden_dim)
        self.dropout = nn.Dropout(dropout)
        
    def chunked_attention(
        self,
        Q: torch.Tensor,
        K: torch.Tensor,
        V: torch.Tensor,
        chunk_size: int
    ) -> torch.Tensor:
        """Process attention in chunks to save memory"""
        batch_size, num_heads, seq_len, head_dim = Q.shape
        
        # Initialize output
        output = torch.zeros_like(Q)
        
        # Process in chunks
        for i in range(0, seq_len, chunk_size):
            end_i = min(i + chunk_size, seq_len)
            Q_chunk = Q[:, :, i:end_i]
            
            # Initialize chunk output
            chunk_output = torch.zeros_like(Q_chunk)
            exp_sum = torch.zeros(batch_size, num_heads, end_i - i, 1, device=Q.device)
            
            for j in range(0, seq_len, chunk_size):
                end_j = min(j + chunk_size, seq_len)
                K_chunk = K[:, :, j:end_j]
                V_chunk = V[:, :, j:end_j]
                
                # Compute attention scores for chunk
                scores = torch.matmul(Q_chunk, K_chunk.transpose(-2, -1))
                scores = scores / (self.head_dim ** 0.5)
                
                # Stable softmax computation
                scores_max = scores.max(dim=-1, keepdim=True)[0]
                scores_exp = torch.exp(scores - scores_max)
                
                # Update running statistics
                exp_sum_chunk = scores_exp.sum(dim=-1, keepdim=True)
                chunk_output = chunk_output * (exp_sum / (exp_sum + exp_sum_chunk))
                chunk_output += torch.matmul(scores_exp / (exp_sum + exp_sum_chunk), V_chunk)
                exp_sum = exp_sum + exp_sum_chunk
            
            output[:, :, i:end_i] = chunk_output
        
        return output
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len, _ = x.shape
        
        # Generate QKV
        qkv = self.qkv(x)
        Q, K, V = rearrange(qkv, 'b n (three h d) -> three b h n d',
                           three=3, h=self.num_heads)
        
        # Apply chunked attention
        context = self.chunked_attention(Q, K, V, self.chunk_size)
        context = rearrange(context, 'b h n d -> b n (h d)')
        
        return self.out_proj(context)


class LinformerAttention(nn.Module):
    """
    Linear complexity attention using low-rank approximation
    Reduces sequence length dimension for efficiency
    """
    
    def __init__(
        self,
        hidden_dim: int,
        num_heads: int = 8,
        seq_len: int = 512,
        projection_dim: int = 64,
        dropout: float = 0.1
    ):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads
        self.projection_dim = projection_dim
        
        # Low-rank projections for K and V
        self.E = nn.Parameter(torch.randn(seq_len, projection_dim))
        self.F = nn.Parameter(torch.randn(seq_len, projection_dim))
        
        self.qkv = nn.Linear(hidden_dim, 3 * hidden_dim)
        self.out_proj = nn.Linear(hidden_dim, hidden_dim)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len, _ = x.shape
        
        # Generate QKV
        qkv = self.qkv(x)
        Q, K, V = rearrange(qkv, 'b n (three h d) -> three b h n d',
                           three=3, h=self.num_heads)
        
        # Project K and V to lower dimension
        K_proj = torch.matmul(self.E[:seq_len, :].T, K.transpose(-2, -1))
        V_proj = torch.matmul(self.F[:seq_len, :].T, V.transpose(-2, -1))
        
        # Compute attention with projected K and V
        scores = torch.matmul(Q, K_proj.transpose(-2, -1)) / (self.head_dim ** 0.5)
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        context = torch.matmul(attn_weights, V_proj.transpose(-2, -1))
        context = rearrange(context, 'b h n d -> b n (h d)')
        
        return self.out_proj(context)


class AttentionPool(nn.Module):
    """
    Attention pooling mechanism for aggregating sequence representations
    Learns to weight different positions based on content
    """
    
    def __init__(self, hidden_dim: int, pool_size: int = 1):
        super().__init__()
        self.pool_size = pool_size
        
        # Learnable query vectors for pooling
        self.pool_queries = nn.Parameter(
            torch.randn(1, pool_size, hidden_dim)
        )
        
        self.attention = nn.MultiheadAttention(
            hidden_dim,
            num_heads=8,
            batch_first=True
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size = x.shape[0]
        
        # Expand pool queries for batch
        queries = self.pool_queries.expand(batch_size, -1, -1)
        
        # Apply attention pooling
        pooled, _ = self.attention(queries, x, x)
        
        if self.pool_size == 1:
            pooled = pooled.squeeze(1)
        
        return pooled


class MultiModalAttentionRouter(nn.Module):
    """
    Routes attention between different modalities dynamically
    Learns optimal attention patterns for multimodal fusion
    """
    
    def __init__(
        self,
        modality_dims: Dict[str, int],
        hidden_dim: int,
        num_heads: int = 8,
        dropout: float = 0.1
    ):
        super().__init__()
        self.modality_dims = modality_dims
        self.hidden_dim = hidden_dim
        
        # Modality-specific attention modules
        self.modality_attention = nn.ModuleDict({
            f"{mod1}_to_{mod2}": MultiHeadCrossModalAttention(
                query_dim=dim1,
                key_dim=dim2,
                value_dim=dim2,
                output_dim=hidden_dim,
                num_heads=num_heads,
                dropout=dropout
            )
            for mod1, dim1 in modality_dims.items()
            for mod2, dim2 in modality_dims.items()
        })
        
        # Routing network
        self.router = nn.ModuleDict({
            mod: nn.Sequential(
                nn.Linear(dim, 128),
                nn.ReLU(),
                nn.Linear(128, len(modality_dims)),
                nn.Softmax(dim=-1)
            )
            for mod, dim in modality_dims.items()
        })
        
        # Output projections
        self.output_projections = nn.ModuleDict({
            mod: nn.Linear(hidden_dim * len(modality_dims), hidden_dim)
            for mod in modality_dims.keys()
        })
        
    def forward(
        self,
        features: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        
        output_features = {}
        
        for query_mod, query_feat in features.items():
            # Get routing weights
            query_pooled = query_feat.mean(dim=1)  # Global pooling
            routing_weights = self.router[query_mod](query_pooled)
            
            # Attend to each modality
            attended_features = []
            for i, (key_mod, key_feat) in enumerate(features.items()):
                attention_key = f"{query_mod}_to_{key_mod}"
                attended = self.modality_attention[attention_key](
                    query_feat, key_feat, key_feat
                )
                # Weight by routing
                weight = routing_weights[:, i:i+1].unsqueeze(1)
                attended = attended * weight
                attended_features.append(attended)
            
            # Combine attended features
            combined = torch.cat(attended_features, dim=-1)
            output_features[query_mod] = self.output_projections[query_mod](combined)
        
        return output_features


# Example usage and testing
if __name__ == "__main__":
    print("Testing Attention Mechanisms")
    print("=" * 50)
    
    batch_size = 2
    seq_len = 100
    hidden_dim = 512
    
    # Test input
    x = torch.randn(batch_size, seq_len, hidden_dim)
    
    # Test each attention mechanism
    attention_modules = [
        ("Cross-Modal Attention", MultiHeadCrossModalAttention(
            hidden_dim, hidden_dim, hidden_dim, hidden_dim
        )),
        ("Sparse Attention", SparseAttention(hidden_dim)),
        ("Local-Global Attention", LocalGlobalAttention(hidden_dim)),
        ("Memory-Augmented Attention", MemoryAugmentedAttention(hidden_dim)),
        ("Channel Attention", ChannelAttention(hidden_dim)),
        ("Spatial Attention", SpatialAttention()),
        ("Temporal Attention", TemporalAttention(hidden_dim)),
        ("Flash Attention", FlashAttention(hidden_dim)),
        ("Linformer Attention", LinformerAttention(hidden_dim, seq_len=seq_len)),
        ("Attention Pooling", AttentionPool(hidden_dim))
    ]
    
    for name, module in attention_modules:
        print(f"\n{name}:")
        try:
            if name == "Cross-Modal Attention":
                output = module(x, x, x)
            elif name == "Attention Pooling":
                output = module(x)
                print(f"  Output shape: {output.shape} (pooled)")
            else:
                output = module(x)
            
            if output.shape != x.shape and name != "Attention Pooling":
                print(f"  Output shape: {output.shape}")
            else:
                print(f"  ✓ Output shape: {output.shape}")
            
            params = sum(p.numel() for p in module.parameters())
            print(f"  ✓ Parameters: {params:,}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Test Multimodal Attention Router
    print("\n" + "=" * 50)
    print("Testing Multimodal Attention Router:")
    
    modality_dims = {
        "text": 768,
        "image": 512,
        "audio": 256
    }
    
    features = {
        "text": torch.randn(batch_size, 50, 768),
        "image": torch.randn(batch_size, 196, 512),
        "audio": torch.randn(batch_size, 100, 256)
    }
    
    router = MultiModalAttentionRouter(modality_dims, hidden_dim)
    routed_features = router(features)
    
    print("\nRouted features:")
    for mod, feat in routed_features.items():
        print(f"  {mod}: {feat.shape}")
    
    print(f"\nTotal router parameters: {sum(p.numel() for p in router.parameters()):,}
