"""
Advanced Fusion Strategies for Multimodal AI
Implementation of fusion techniques for combining multiple modalities
Including hierarchical, adaptive, and attention-based fusion strategies.
Date: 10/72025
CA
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
from enum import Enum
import math
from dataclasses import dataclass


@dataclass
class FusionConfig:
    """Configuration for fusion strategies"""
    strategy: str
    hidden_dim: int
    num_modalities: int
    dropout_rate: float = 0.1
    use_gate: bool = True
    use_residual: bool = True
    temperature: float = 1.0
    alignment_loss_weight: float = 0.1


class FusionType(Enum):
    """Types of fusion strategies"""
    CONCATENATION = "concatenation"
    ADDITION = "addition"
    MULTIPLICATION = "multiplication"
    ATTENTION = "attention"
    GATED = "gated"
    BILINEAR = "bilinear"
    TUCKER = "tucker"
    HIERARCHICAL = "hierarchical"
    ADAPTIVE = "adaptive"
    TRANSFORMER = "transformer"
    GRAPH = "graph"
    TENSOR = "tensor"


class ModalityAlignment(nn.Module):
    """
    Aligns different modalities to a common representation space
    Uses contrastive learning and projection networks
    """
    
    def __init__(self, modality_dims: Dict[str, int], aligned_dim: int):
        super().__init__()
        
        # Projection networks for each modality
        self.projectors = nn.ModuleDict({
            name: nn.Sequential(
                nn.Linear(dim, aligned_dim * 2),
                nn.LayerNorm(aligned_dim * 2),
                nn.GELU(),
                nn.Dropout(0.1),
                nn.Linear(aligned_dim * 2, aligned_dim),
                nn.LayerNorm(aligned_dim)
            )
            for name, dim in modality_dims.items()
        })
        
        # Learnable temperature for contrastive loss
        self.temperature = nn.Parameter(torch.ones(1) * 0.07)
        
    def forward(self, features: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Project all modalities to aligned space"""
        aligned = {}
        for name, feat in features.items():
            if name in self.projectors:
                # Global pooling if needed
                if len(feat.shape) > 2:
                    feat = feat.mean(dim=1)  # Pool sequence dimension
                aligned[name] = F.normalize(self.projectors[name](feat), dim=-1)
        return aligned
    
    def alignment_loss(self, aligned_features: Dict[str, torch.Tensor]) -> torch.Tensor:
        """Calculate contrastive alignment loss between modality pairs"""
        losses = []
        modality_names = list(aligned_features.keys())
        
        for i in range(len(modality_names)):
            for j in range(i + 1, len(modality_names)):
                feat_a = aligned_features[modality_names[i]]
                feat_b = aligned_features[modality_names[j]]
                
                # Contrastive loss
                logits = torch.matmul(feat_a, feat_b.T) / self.temperature
                labels = torch.arange(len(feat_a), device=feat_a.device)
                
                loss_a = F.cross_entropy(logits, labels)
                loss_b = F.cross_entropy(logits.T, labels)
                losses.append((loss_a + loss_b) / 2)
        
        return torch.stack(losses).mean() if losses else torch.tensor(0.0)


class ConcatenationFusion(nn.Module):
    """Simple concatenation-based fusion with projection"""
    
    def __init__(self, input_dims: List[int], output_dim: int):
        super().__init__()
        total_dim = sum(input_dims)
        self.projection = nn.Sequential(
            nn.Linear(total_dim, output_dim * 2),
            nn.LayerNorm(output_dim * 2),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(output_dim * 2, output_dim)
        )
    
    def forward(self, features: List[torch.Tensor]) -> torch.Tensor:
        concatenated = torch.cat(features, dim=-1)
        return self.projection(concatenated)


class GatedFusion(nn.Module):
    """
    Gated fusion mechanism that learns importance weights for each modality
    Based on the Gated Multimodal Unit (GMU) architecture
    """
    
    def __init__(self, modality_dims: Dict[str, int], output_dim: int):
        super().__init__()
        
        # Gates for each modality
        self.gates = nn.ModuleDict({
            name: nn.Sequential(
                nn.Linear(dim, output_dim),
                nn.LayerNorm(output_dim),
                nn.Sigmoid()
            )
            for name, dim in modality_dims.items()
        })
        
        # Transform each modality
        self.transforms = nn.ModuleDict({
            name: nn.Linear(dim, output_dim)
            for name, dim in modality_dims.items()
        })
        
        self.output_norm = nn.LayerNorm(output_dim)
        
    def forward(self, features: Dict[str, torch.Tensor]) -> torch.Tensor:
        gated_features = []
        
        for name, feat in features.items():
            # Calculate gate values
            gate = self.gates[name](feat)
            # Transform features
            transformed = self.transforms[name](feat)
            # Apply gating
            gated = gate * transformed
            gated_features.append(gated)
        
        # Sum gated features
        fused = torch.stack(gated_features, dim=0).sum(dim=0)
        return self.output_norm(fused)


class BilinearFusion(nn.Module):
    """
    Bilinear pooling fusion for capturing second-order interactions
    Efficient implementation using low-rank approximation
    """
    
    def __init__(self, dim1: int, dim2: int, output_dim: int, rank: int = 32):
        super().__init__()
        self.rank = rank
        
        # Low-rank decomposition
        self.U1 = nn.Linear(dim1, rank, bias=False)
        self.U2 = nn.Linear(dim2, rank, bias=False)
        self.P = nn.Linear(rank, output_dim)
        
        self.dropout = nn.Dropout(0.1)
        self.norm = nn.LayerNorm(output_dim)
        
    def forward(self, x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
        # Low-rank bilinear pooling
        h1 = self.U1(x1)  # [batch, seq, rank]
        h2 = self.U2(x2)  # [batch, seq, rank]
        
        # Element-wise multiplication (Hadamard product)
        fusion = h1 * h2  # [batch, seq, rank]
        
        # Final projection
        output = self.P(fusion)
        output = self.dropout(output)
        return self.norm(output)


class TuckerFusion(nn.Module):
    """
    Tucker decomposition-based fusion for tensor-based multimodal fusion
    Captures high-order interactions between modalities
    """
    
    def __init__(self, modality_dims: List[int], output_dim: int, rank: int = 16):
        super().__init__()
        self.n_modalities = len(modality_dims)
        self.rank = rank
        
        # Factor matrices for each modality
        self.factors = nn.ModuleList([
            nn.Linear(dim, rank) for dim in modality_dims
        ])
        
        # Core tensor (learned)
        core_shape = [rank] * self.n_modalities + [output_dim]
        self.core = nn.Parameter(torch.randn(*core_shape) * 0.01)
        
        self.norm = nn.LayerNorm(output_dim)
        
    def forward(self, features: List[torch.Tensor]) -> torch.Tensor:
        batch_size = features[0].shape[0]
        seq_len = features[0].shape[1] if len(features[0].shape) > 2 else 1
        
        # Project each modality
        projected = []
        for i, feat in enumerate(features):
            if len(feat.shape) == 2:
                feat = feat.unsqueeze(1)
            proj = self.factors[i](feat)  # [batch, seq, rank]
            projected.append(proj)
        
        # Compute Tucker product
        result = self.core.clone()
        
        for i, proj in enumerate(projected):
            # Contract along each mode
            result = torch.tensordot(proj, result, dims=([2], [i]))
            # Move batch and seq dimensions to front
            dims = list(range(len(result.shape)))
            dims = [dims[-2], dims[-1]] + dims[:-2]
            result = result.permute(*dims)
        
        # Final shape: [batch, seq, output_dim]
        result = result.reshape(batch_size, -1, result.shape[-1])
        return self.norm(result)


class HierarchicalFusion(nn.Module):
    """
    Hierarchical fusion that combines modalities at multiple scales
    Inspired by Feature Pyramid Networks
    """
    
    def __init__(self, modality_dims: Dict[str, int], hidden_dims: List[int]):
        super().__init__()
        self.levels = len(hidden_dims)
        
        # Multi-level projections for each modality
        self.projections = nn.ModuleDict()
        for name, input_dim in modality_dims.items():
            level_projections = nn.ModuleList()
            current_dim = input_dim
            
            for hidden_dim in hidden_dims:
                level_projections.append(
                    nn.Sequential(
                        nn.Linear(current_dim, hidden_dim),
                        nn.LayerNorm(hidden_dim),
                        nn.GELU()
                    )
                )
                current_dim = hidden_dim
            
            self.projections[name] = level_projections
        
        # Cross-level attention
        self.cross_level_attention = nn.ModuleList([
            nn.MultiheadAttention(hidden_dim, num_heads=8, batch_first=True)
            for hidden_dim in hidden_dims
        ])
        
        # Level-wise fusion
        self.level_fusion = nn.ModuleList([
            GatedFusion(
                {name: hidden_dim for name in modality_dims.keys()}, 
                hidden_dim
            )
            for hidden_dim in hidden_dims
        ])
        
        # Final aggregation
        self.final_fusion = nn.Sequential(
            nn.Linear(sum(hidden_dims), hidden_dims[-1]),
            nn.LayerNorm(hidden_dims[-1]),
            nn.GELU()
        )
        
    def forward(self, features: Dict[str, torch.Tensor]) -> torch.Tensor:
        level_outputs = []
        
        for level in range(self.levels):
            # Project each modality to current level
            level_features = {}
            for name, feat in features.items():
                projected = self.projections[name][level](feat)
                level_features[name] = projected
            
            # Fuse at current level
            fused = self.level_fusion[level](level_features)
            
            # Apply cross-level attention if not first level
            if level > 0 and level_outputs:
                prev_level = level_outputs[-1]
                fused, _ = self.cross_level_attention[level](
                    fused, prev_level, prev_level
                )
            
            level_outputs.append(fused)
        
        # Combine all levels
        combined = torch.cat(level_outputs, dim=-1)
        return self.final_fusion(combined)


class AdaptiveFusion(nn.Module):
    """
    Adaptive fusion that dynamically selects fusion strategy based on input
    Uses meta-learning to choose optimal fusion per sample
    """
    
    def __init__(self, modality_dims: Dict[str, int], output_dim: int):
        super().__init__()
        
        # Multiple fusion strategies
        self.fusion_strategies = nn.ModuleDict({
            'concat': ConcatenationFusion(list(modality_dims.values()), output_dim),
            'gated': GatedFusion(modality_dims, output_dim),
            'bilinear': BilinearFusion(
                list(modality_dims.values())[0], 
                list(modality_dims.values())[1] if len(modality_dims) > 1 else list(modality_dims.values())[0],
                output_dim
            )
        })
        
        # Meta-network to predict fusion weights
        total_dim = sum(modality_dims.values())
        self.meta_network = nn.Sequential(
            nn.Linear(total_dim, 128),
            nn.ReLU(),
            nn.Linear(128, len(self.fusion_strategies)),
            nn.Softmax(dim=-1)
        )
        
    def forward(self, features: Dict[str, torch.Tensor]) -> torch.Tensor:
        # Flatten and concatenate features for meta-network
        flattened = []
        features_list = []
        
        for name, feat in features.items():
            if len(feat.shape) > 2:
                feat_flat = feat.mean(dim=1)  # Global pooling
            else:
                feat_flat = feat
            flattened.append(feat_flat)
            features_list.append(feat)
        
        meta_input = torch.cat(flattened, dim=-1)
        
        # Get fusion weights
        fusion_weights = self.meta_network(meta_input).unsqueeze(-1)
        
        # Apply each fusion strategy
        fusion_outputs = []
        
        if 'concat' in self.fusion_strategies:
            concat_out = self.fusion_strategies['concat'](features_list)
            fusion_outputs.append(concat_out)
        
        if 'gated' in self.fusion_strategies:
            gated_out = self.fusion_strategies['gated'](features)
            fusion_outputs.append(gated_out)
        
        if 'bilinear' in self.fusion_strategies and len(features_list) >= 2:
            bilinear_out = self.fusion_strategies['bilinear'](
                features_list[0], features_list[1]
            )
            fusion_outputs.append(bilinear_out)
        
        # Weighted combination
        fusion_outputs = torch.stack(fusion_outputs, dim=1)  # [batch, n_strategies, seq, dim]
        
        # Expand weights for broadcasting
        if len(fusion_outputs.shape) == 4:
            fusion_weights = fusion_weights.unsqueeze(-1)
        
        weighted_output = (fusion_outputs * fusion_weights).sum(dim=1)
        
        return weighted_output


class TransformerFusion(nn.Module):
    """
    Transformer-based fusion with cross-modal attention
    Treats each modality as a sequence and uses self-attention for fusion
    """
    
    def __init__(
        self, 
        modality_dims: Dict[str, int], 
        output_dim: int,
        num_layers: int = 3,
        num_heads: int = 8
    ):
        super().__init__()
        
        # Project all modalities to same dimension
        self.projections = nn.ModuleDict({
            name: nn.Linear(dim, output_dim)
            for name, dim in modality_dims.items()
        })
        
        # Modality embeddings
        self.modality_embeddings = nn.ParameterDict({
            name: nn.Parameter(torch.randn(1, 1, output_dim) * 0.02)
            for name in modality_dims.keys()
        })
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=output_dim,
            nhead=num_heads,
            dim_feedforward=output_dim * 4,
            dropout=0.1,
            activation='gelu',
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Output projection
        self.output_projection = nn.Linear(output_dim, output_dim)
        
    def forward(self, features: Dict[str, torch.Tensor]) -> torch.Tensor:
        projected_features = []
        
        for name, feat in features.items():
            # Project to common dimension
            proj = self.projections[name](feat)
            
            # Add modality embedding
            modality_emb = self.modality_embeddings[name].expand(
                feat.shape[0], feat.shape[1] if len(feat.shape) > 2 else 1, -1
            )
            proj = proj + modality_emb
            
            projected_features.append(proj)
        
        # Concatenate all modalities along sequence dimension
        combined = torch.cat(projected_features, dim=1)
        
        # Apply transformer
        fused = self.transformer(combined)
        
        # Apply output projection
        output = self.output_projection(fused)
        
        return output


class GraphFusion(nn.Module):
    """
    Graph-based fusion that models modalities as nodes in a graph
    Uses Graph Neural Networks for information propagation
    """
    
    def __init__(self, modality_dims: Dict[str, int], output_dim: int):
        super().__init__()
        self.modality_names = list(modality_dims.keys())
        self.n_modalities = len(self.modality_names)
        
        # Node feature projection
        self.node_projections = nn.ModuleDict({
            name: nn.Linear(dim, output_dim)
            for name, dim in modality_dims.items()
        })
        
        # Edge features (learnable adjacency matrix)
        self.adjacency = nn.Parameter(torch.ones(self.n_modalities, self.n_modalities) * 0.1)
        
        # Graph convolution layers
        self.graph_convs = nn.ModuleList([
            GraphConvLayer(output_dim, output_dim)
            for _ in range(3)
        ])
        
        # Readout
        self.readout = nn.Sequential(
            nn.Linear(output_dim * self.n_modalities, output_dim),
            nn.LayerNorm(output_dim),
            nn.GELU()
        )
        
    def forward(self, features: Dict[str, torch.Tensor]) -> torch.Tensor:
        batch_size = next(iter(features.values())).shape[0]
        
        # Project node features
        node_features = []
        for name in self.modality_names:
            feat = features[name]
            if len(feat.shape) > 2:
                feat = feat.mean(dim=1)  # Global pooling
            proj = self.node_projections[name](feat)
            node_features.append(proj)
        
        node_features = torch.stack(node_features, dim=1)  # [batch, n_nodes, dim]
        
        # Get adjacency matrix with self-loops
        adj = F.softmax(self.adjacency, dim=-1)
        adj = adj + torch.eye(self.n_modalities, device=adj.device)
        
        # Apply graph convolutions
        h = node_features
        for conv in self.graph_convs:
            h = conv(h, adj)
        
        # Readout
        h_flat = h.reshape(batch_size, -1)
        output = self.readout(h_flat)
        
        return output.unsqueeze(1)  # Add sequence dimension


class GraphConvLayer(nn.Module):
    """Simple Graph Convolution Layer"""
    
    def __init__(self, input_dim: int, output_dim: int):
        super().__init__()
        self.linear = nn.Linear(input_dim, output_dim)
        self.activation = nn.GELU()
        self.norm = nn.LayerNorm(output_dim)
        
    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        # x: [batch, n_nodes, dim]
        # adj: [n_nodes, n_nodes]
        
        # Graph convolution: H' = σ(AHW)
        h = torch.matmul(adj, x)  # [batch, n_nodes, dim]
        h = self.linear(h)
        h = self.activation(h)
        h = self.norm(h)
        
        return h


class MultiScaleFusion(nn.Module):
    """
    Multi-scale fusion that processes features at different temporal/spatial resolutions
    """
    
    def __init__(self, modality_dims: Dict[str, int], output_dim: int, scales: List[int] = [1, 2, 4]):
        super().__init__()
        self.scales = scales
        
        # Multi-scale processing for each modality
        self.scale_processors = nn.ModuleDict()
        for name, dim in modality_dims.items():
            scale_modules = nn.ModuleList()
            for scale in scales:
                if scale == 1:
                    module = nn.Identity()
                else:
                    module = nn.Sequential(
                        nn.AvgPool1d(kernel_size=scale, stride=scale),
                        nn.Conv1d(dim, dim, kernel_size=1)
                    )
                scale_modules.append(module)
            self.scale_processors[name] = scale_modules
        
        # Fusion at each scale
        self.scale_fusion = nn.ModuleList([
            GatedFusion(modality_dims, output_dim)
            for _ in scales
        ])
        
        # Combine scales
        self.combine_scales = nn.Sequential(
            nn.Linear(output_dim * len(scales), output_dim),
            nn.LayerNorm(output_dim),
            nn.GELU()
        )
        
    def forward(self, features: Dict[str, torch.Tensor]) -> torch.Tensor:
        scale_outputs = []
        
        for i, scale in enumerate(self.scales):
            scale_features = {}
            
            for name, feat in features.items():
                # Process at current scale
                if scale > 1:
                    # Reshape for pooling
                    batch, seq, dim = feat.shape
                    feat = feat.transpose(1, 2)  # [batch, dim, seq]
                    feat = self.scale_processors[name][i](feat)
                    feat = feat.transpose(1, 2)  # [batch, seq, dim]
                
                scale_features[name] = feat
            
            # Fuse at current scale
            fused = self.scale_fusion[i](scale_features)
            
            # Upsample to original size if needed
            if scale > 1:
                fused = F.interpolate(
                    fused.transpose(1, 2), 
                    size=features[list(features.keys())[0]].shape[1],
                    mode='linear',
                    align_corners=False
                ).transpose(1, 2)
            
            scale_outputs.append(fused)
        
        # Combine all scales
        combined = torch.cat(scale_outputs, dim=-1)
        return self.combine_scales(combined)


class FusionFactory:
    """Factory class for creating fusion modules"""
    
    @staticmethod
    def create_fusion(
        fusion_type: Union[str, FusionType],
        modality_dims: Dict[str, int],
        output_dim: int,
        **kwargs
    ) -> nn.Module:
        """
        Create a fusion module based on the specified type
        
        Args:
            fusion_type: Type of fusion strategy
            modality_dims: Dictionary mapping modality names to dimensions
            output_dim: Output dimension
            **kwargs: Additional arguments for specific fusion types
        
        Returns:
            Fusion module
        """
        
        if isinstance(fusion_type, str):
            fusion_type = FusionType(fusion_type)
        
        if fusion_type == FusionType.CONCATENATION:
            return ConcatenationFusion(list(modality_dims.values()), output_dim)
        
        elif fusion_type == FusionType.GATED:
            return GatedFusion(modality_dims, output_dim)
        
        elif fusion_type == FusionType.BILINEAR:
            dims = list(modality_dims.values())
            return BilinearFusion(
                dims[0], 
                dims[1] if len(dims) > 1 else dims[0],
                output_dim,
                rank=kwargs.get('rank', 32)
            )
        
        elif fusion_type == FusionType.TUCKER:
            return TuckerFusion(
                list(modality_dims.values()),
                output_dim,
                rank=kwargs.get('rank', 16)
            )
        
        elif fusion_type == FusionType.HIERARCHICAL:
            hidden_dims = kwargs.get('hidden_dims', [256, 512, 768])
            return HierarchicalFusion(modality_dims, hidden_dims)
        
        elif fusion_type == FusionType.ADAPTIVE:
            return AdaptiveFusion(modality_dims, output_dim)
        
        elif fusion_type == FusionType.TRANSFORMER:
            return TransformerFusion(
                modality_dims,
                output_dim,
                num_layers=kwargs.get('num_layers', 3),
                num_heads=kwargs.get('num_heads', 8)
            )
        
        elif fusion_type == FusionType.GRAPH:
            return GraphFusion(modality_dims, output_dim)
        
        else:
            raise ValueError(f"Unsupported fusion type: {fusion_type}")


# Example usage and testing
if __name__ == "__main__":
    # Test configurations
    modality_dims = {
        'text': 768,
        'image': 2048,
        'audio': 128
    }
    output_dim = 512
    batch_size = 4
    
    # Create test data
    test_features = {
        'text': torch.randn(batch_size, 50, 768),
        'image': torch.randn(batch_size, 196, 2048),
        'audio': torch.randn(batch_size, 100, 128)
    }
    
    # Test each fusion strategy
    fusion_types = [
        FusionType.GATED,
        FusionType.HIERARCHICAL,
        FusionType.ADAPTIVE,
        FusionType.TRANSFORMER,
        FusionType.GRAPH
    ]
    
    print("Testing Fusion Strategies:")
    print("-" * 50)
    
    for fusion_type in fusion_types:
        print(f"\nTesting {fusion_type.value} fusion:")
        
        # Create fusion module
        fusion_module = FusionFactory.create_fusion(
            fusion_type,
            modality_dims,
            output_dim
        )
        
        # Forward pass
        try:
            output = fusion_module(test_features)
            print(f"  ✓ Output shape: {output.shape}")
            print(f"  ✓ Parameters: {sum(p.numel() for p in fusion_module.parameters()):,}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n" + "=" * 50)
    print("Testing Alignment Module:")
    
    # Test alignment module
    alignment = ModalityAlignment(modality_dims, output_dim)
    aligned_features = alignment(test_features)
    alignment_loss = alignment.alignment_loss(aligned_features)
    
    print(f"Aligned features:")
    for name, feat in aligned_features.items():
        print(f"  {name}: {feat.shape}")
    print(f"Alignment loss: {alignment_loss.item():.4f}")
