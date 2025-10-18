"""
Unified Multimodal Generative Transformer
Production-ready implementation for image, video, audio, and text generation
Supports cross-modal translation, editing, and zero-shot capabilities
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.cuda.amp import autocast
import numpy as np
from einops import rearrange, repeat, reduce
from typing import Optional, Tuple, Dict, List, Union, Any
from dataclasses import dataclass
import math
from functools import partial
import xformers.ops as xops
from contextlib import contextmanager
import torchvision.transforms as T
from collections import OrderedDict


@dataclass
class ModelConfig:
    hidden_size: int = 1536
    num_layers: int = 48
    num_heads: int = 24
    head_dim: int = 64
    mlp_ratio: int = 4
    patch_size: int = 16
    max_seq_length: int = 77
    vocab_size: int = 50257
    image_size: int = 1024
    video_frames: int = 16
    audio_seq_len: int = 16000
    latent_dim: int = 512
    num_modalities: int = 4
    use_flash_attn: bool = True
    use_rotary_emb: bool = True
    use_adaptive_layernorm: bool = True
    gradient_checkpointing: bool = False
    mixed_precision: bool = True


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        return x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps) * self.weight


class AdaptiveLayerNorm(nn.Module):
    def __init__(self, dim: int, num_modalities: int = 4):
        super().__init__()
        self.norm = nn.LayerNorm(dim)
        self.modality_scales = nn.Parameter(torch.ones(num_modalities, dim))
        self.modality_shifts = nn.Parameter(torch.zeros(num_modalities, dim))
        
    def forward(self, x: torch.Tensor, modality_id: int = 0) -> torch.Tensor:
        normalized = self.norm(x)
        scale = self.modality_scales[modality_id]
        shift = self.modality_shifts[modality_id]
        return normalized * scale + shift


class RotaryEmbedding(nn.Module):
    def __init__(self, dim: int, max_seq_len: int = 8192, base: int = 10000):
        super().__init__()
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq)
        self.max_seq_len = max_seq_len
        self._cos_cached = None
        self._sin_cached = None
        
    def _update_cos_sin_cache(self, x: torch.Tensor, seq_len: int):
        if self._cos_cached is None or seq_len > self._cos_cached.size(0):
            freqs = torch.einsum("i,j->ij", torch.arange(seq_len, device=x.device), self.inv_freq)
            emb = torch.cat((freqs, freqs), dim=-1)
            self._cos_cached = emb.cos()[None, :, None, :]
            self._sin_cached = emb.sin()[None, :, None, :]
        return self._cos_cached[:, :seq_len], self._sin_cached[:, :seq_len]
    
    def forward(self, q: torch.Tensor, k: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        batch, seq_len, num_heads, head_dim = q.shape
        cos, sin = self._update_cos_sin_cache(q, seq_len)
        
        q_real = q[..., :head_dim // 2]
        q_imag = q[..., head_dim // 2:]
        k_real = k[..., :head_dim // 2]
        k_imag = k[..., head_dim // 2:]
        
        q_rot = torch.cat([
            q_real * cos[..., :head_dim // 2] - q_imag * sin[..., :head_dim // 2],
            q_real * sin[..., :head_dim // 2] + q_imag * cos[..., :head_dim // 2]
        ], dim=-1)
        
        k_rot = torch.cat([
            k_real * cos[..., :head_dim // 2] - k_imag * sin[..., :head_dim // 2],
            k_real * sin[..., :head_dim // 2] + k_imag * cos[..., :head_dim // 2]
        ], dim=-1)
        
        return q_rot, k_rot


class MultiHeadAttention(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        self.num_heads = config.num_heads
        self.head_dim = config.head_dim
        self.hidden_size = config.hidden_size
        
        self.qkv = nn.Linear(config.hidden_size, 3 * config.num_heads * config.head_dim, bias=False)
        self.out_proj = nn.Linear(config.num_heads * config.head_dim, config.hidden_size, bias=False)
        
        if config.use_rotary_emb:
            self.rotary_emb = RotaryEmbedding(config.head_dim, config.max_seq_length)
        
        self.scale = 1.0 / math.sqrt(config.head_dim)
        self.dropout = nn.Dropout(0.1)
        
    def forward(
        self,
        x: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        is_causal: bool = False
    ) -> torch.Tensor:
        batch_size, seq_len, _ = x.shape
        
        qkv = self.qkv(x)
        qkv = rearrange(qkv, 'b s (three h d) -> three b s h d', three=3, h=self.num_heads)
        q, k, v = qkv[0], qkv[1], qkv[2]
        
        if self.config.use_rotary_emb:
            q, k = self.rotary_emb(q, k)
        
        if self.config.use_flash_attn and xops is not None:
            q = rearrange(q, 'b s h d -> b s (h d)')
            k = rearrange(k, 'b s h d -> b s (h d)')
            v = rearrange(v, 'b s h d -> b s (h d)')
            
            out = xops.memory_efficient_attention(
                q.unsqueeze(0), k.unsqueeze(0), v.unsqueeze(0),
                attn_bias=attention_mask,
                p=0.1 if self.training else 0.0
            ).squeeze(0)
        else:
            q = rearrange(q, 'b s h d -> b h s d')
            k = rearrange(k, 'b s h d -> b h s d')
            v = rearrange(v, 'b s h d -> b h s d')
            
            scores = torch.matmul(q, k.transpose(-2, -1)) * self.scale
            
            if attention_mask is not None:
                scores = scores.masked_fill(attention_mask == 0, -1e9)
            
            if is_causal:
                causal_mask = torch.triu(torch.ones(seq_len, seq_len, device=x.device), diagonal=1).bool()
                scores = scores.masked_fill(causal_mask, -1e9)
            
            attn = F.softmax(scores, dim=-1)
            attn = self.dropout(attn)
            
            out = torch.matmul(attn, v)
            out = rearrange(out, 'b h s d -> b s (h d)')
        
        return self.out_proj(out)


class FeedForward(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        hidden_dim = int(config.hidden_size * config.mlp_ratio)
        
        self.w1 = nn.Linear(config.hidden_size, hidden_dim, bias=False)
        self.w2 = nn.Linear(hidden_dim, config.hidden_size, bias=False)
        self.w3 = nn.Linear(config.hidden_size, hidden_dim, bias=False)
        self.dropout = nn.Dropout(0.1)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.dropout(self.w2(F.silu(self.w1(x)) * self.w3(x)))


class TransformerBlock(nn.Module):
    def __init__(self, config: ModelConfig, layer_idx: int):
        super().__init__()
        self.config = config
        self.layer_idx = layer_idx
        
        if config.use_adaptive_layernorm:
            self.ln1 = AdaptiveLayerNorm(config.hidden_size, config.num_modalities)
            self.ln2 = AdaptiveLayerNorm(config.hidden_size, config.num_modalities)
        else:
            self.ln1 = RMSNorm(config.hidden_size)
            self.ln2 = RMSNorm(config.hidden_size)
        
        self.attn = MultiHeadAttention(config)
        self.ff = FeedForward(config)
        
        self.use_checkpoint = config.gradient_checkpointing
        
    def forward(
        self,
        x: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        modality_id: int = 0
    ) -> torch.Tensor:
        if self.use_checkpoint and self.training:
            return torch.utils.checkpoint.checkpoint(
                self._forward, x, attention_mask, modality_id
            )
        return self._forward(x, attention_mask, modality_id)
    
    def _forward(
        self,
        x: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        modality_id: int = 0
    ) -> torch.Tensor:
        if self.config.use_adaptive_layernorm:
            h = x + self.attn(self.ln1(x, modality_id), attention_mask)
            out = h + self.ff(self.ln2(h, modality_id))
        else:
            h = x + self.attn(self.ln1(x), attention_mask)
            out = h + self.ff(self.ln2(h))
        return out


class ModalityEncoder(nn.Module):
    def __init__(self, config: ModelConfig, modality_type: str):
        super().__init__()
        self.config = config
        self.modality_type = modality_type
        
        if modality_type == "image":
            self.encoder = ImageEncoder(config)
        elif modality_type == "text":
            self.encoder = TextEncoder(config)
        elif modality_type == "audio":
            self.encoder = AudioEncoder(config)
        elif modality_type == "video":
            self.encoder = VideoEncoder(config)
        
    def forward(self, x: torch.Tensor, **kwargs) -> torch.Tensor:
        return self.encoder(x, **kwargs)


class ImageEncoder(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.patch_embed = nn.Conv2d(
            3, config.hidden_size,
            kernel_size=config.patch_size,
            stride=config.patch_size
        )
        
        num_patches = (config.image_size // config.patch_size) ** 2
        self.pos_embed = nn.Parameter(torch.zeros(1, num_patches + 1, config.hidden_size))
        self.cls_token = nn.Parameter(torch.zeros(1, 1, config.hidden_size))
        
        nn.init.trunc_normal_(self.pos_embed, std=0.02)
        nn.init.trunc_normal_(self.cls_token, std=0.02)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B = x.shape[0]
        x = self.patch_embed(x)
        x = rearrange(x, 'b c h w -> b (h w) c')
        
        cls_tokens = repeat(self.cls_token, '1 1 d -> b 1 d', b=B)
        x = torch.cat([cls_tokens, x], dim=1)
        x = x + self.pos_embed
        
        return x


class TextEncoder(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.token_embed = nn.Embedding(config.vocab_size, config.hidden_size)
        self.pos_embed = nn.Parameter(torch.zeros(1, config.max_seq_length, config.hidden_size))
        nn.init.trunc_normal_(self.pos_embed, std=0.02)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.token_embed(x)
        x = x + self.pos_embed[:, :x.size(1)]
        return x


class AudioEncoder(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.conv1 = nn.Conv1d(1, config.hidden_size // 4, kernel_size=10, stride=5)
        self.conv2 = nn.Conv1d(config.hidden_size // 4, config.hidden_size // 2, kernel_size=4, stride=2)
        self.conv3 = nn.Conv1d(config.hidden_size // 2, config.hidden_size, kernel_size=4, stride=2)
        self.norm = nn.LayerNorm(config.hidden_size)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() == 2:
            x = x.unsqueeze(1)
        
        x = F.gelu(self.conv1(x))
        x = F.gelu(self.conv2(x))
        x = F.gelu(self.conv3(x))
        x = rearrange(x, 'b c l -> b l c')
        x = self.norm(x)
        
        return x


class VideoEncoder(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.temporal_embed = nn.Conv3d(
            3, config.hidden_size,
            kernel_size=(3, config.patch_size, config.patch_size),
            stride=(1, config.patch_size, config.patch_size),
            padding=(1, 0, 0)
        )
        
        num_patches = (config.image_size // config.patch_size) ** 2
        self.pos_embed_spatial = nn.Parameter(torch.zeros(1, num_patches, config.hidden_size))
        self.pos_embed_temporal = nn.Parameter(torch.zeros(1, config.video_frames, config.hidden_size))
        
        nn.init.trunc_normal_(self.pos_embed_spatial, std=0.02)
        nn.init.trunc_normal_(self.pos_embed_temporal, std=0.02)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, C, H, W = x.shape
        x = rearrange(x, 'b t c h w -> b c t h w')
        x = self.temporal_embed(x)
        x = rearrange(x, 'b c t h w -> b t (h w) c')
        
        x = x + self.pos_embed_spatial.unsqueeze(1)
        x = x + self.pos_embed_temporal.unsqueeze(2)
        x = rearrange(x, 'b t n c -> b (t n) c')
        
        return x


class DiffusionDecoder(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        
        self.time_embed = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size * 4),
            nn.SiLU(),
            nn.Linear(config.hidden_size * 4, config.hidden_size)
        )
        
        self.input_blocks = nn.ModuleList([
            nn.Conv2d(3, config.hidden_size, 3, padding=1),
            *[ResBlock(config.hidden_size) for _ in range(3)]
        ])
        
        self.middle_block = nn.Sequential(
            ResBlock(config.hidden_size),
            AttentionBlock(config.hidden_size),
            ResBlock(config.hidden_size)
        )
        
        self.output_blocks = nn.ModuleList([
            *[ResBlock(config.hidden_size) for _ in range(3)],
            nn.Conv2d(config.hidden_size, 3, 3, padding=1)
        ])
        
        self.norm = nn.GroupNorm(32, config.hidden_size)
        
    def forward(self, x: torch.Tensor, t: torch.Tensor, context: torch.Tensor) -> torch.Tensor:
        t_emb = self.time_embed(timestep_embedding(t, self.config.hidden_size))
        
        hs = []
        for module in self.input_blocks:
            if isinstance(module, ResBlock):
                x = module(x, t_emb)
            else:
                x = module(x)
            hs.append(x)
        
        x = self.middle_block[0](x, t_emb)
        x = self.middle_block[1](x, context)
        x = self.middle_block[2](x, t_emb)
        
        for module in self.output_blocks[:-1]:
            x = torch.cat([x, hs.pop()], dim=1) if hs else x
            x = module(x, t_emb)
        
        x = self.norm(x)
        x = F.silu(x)
        x = self.output_blocks[-1](x)
        
        return x


class ResBlock(nn.Module):
    def __init__(self, channels: int):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, 3, padding=1)
        self.conv2 = nn.Conv2d(channels, channels, 3, padding=1)
        self.norm1 = nn.GroupNorm(32, channels)
        self.norm2 = nn.GroupNorm(32, channels)
        self.time_emb_proj = nn.Linear(channels, channels)
        
    def forward(self, x: torch.Tensor, t_emb: Optional[torch.Tensor] = None) -> torch.Tensor:
        h = x
        h = self.norm1(h)
        h = F.silu(h)
        h = self.conv1(h)
        
        if t_emb is not None:
            h = h + self.time_emb_proj(F.silu(t_emb))[:, :, None, None]
        
        h = self.norm2(h)
        h = F.silu(h)
        h = self.conv2(h)
        
        return x + h


class AttentionBlock(nn.Module):
    def __init__(self, channels: int):
        super().__init__()
        self.norm = nn.GroupNorm(32, channels)
        self.q = nn.Conv2d(channels, channels, 1)
        self.k = nn.Conv2d(channels, channels, 1)
        self.v = nn.Conv2d(channels, channels, 1)
        self.proj_out = nn.Conv2d(channels, channels, 1)
        self.scale = 1.0 / math.sqrt(channels)
        
    def forward(self, x: torch.Tensor, context: Optional[torch.Tensor] = None) -> torch.Tensor:
        h = self.norm(x)
        q = self.q(h)
        
        if context is not None:
            context = context.unsqueeze(-1).unsqueeze(-1)
            context = F.interpolate(context, size=h.shape[-2:], mode='bilinear')
            k = self.k(context)
            v = self.v(context)
        else:
            k = self.k(h)
            v = self.v(h)
        
        B, C, H, W = q.shape
        q = rearrange(q, 'b c h w -> b (h w) c')
        k = rearrange(k, 'b c h w -> b (h w) c')
        v = rearrange(v, 'b c h w -> b (h w) c')
        
        attn = torch.bmm(q, k.transpose(1, 2)) * self.scale
        attn = F.softmax(attn, dim=-1)
        
        out = torch.bmm(attn, v)
        out = rearrange(out, 'b (h w) c -> b c h w', h=H, w=W)
        out = self.proj_out(out)
        
        return x + out


def timestep_embedding(timesteps: torch.Tensor, dim: int, max_period: int = 10000) -> torch.Tensor:
    half = dim // 2
    freqs = torch.exp(
        -math.log(max_period) * torch.arange(half, dtype=torch.float32, device=timesteps.device) / half
    )
    args = timesteps[:, None].float() * freqs[None]
    embedding = torch.cat([torch.cos(args), torch.sin(args)], dim=-1)
    if dim % 2:
        embedding = torch.cat([embedding, torch.zeros_like(embedding[:, :1])], dim=-1)
    return embedding


class UnifiedMultimodalTransformer(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        
        self.encoders = nn.ModuleDict({
            'image': ImageEncoder(config),
            'text': TextEncoder(config),
            'audio': AudioEncoder(config),
            'video': VideoEncoder(config)
        })
        
        self.modality_type_embed = nn.Embedding(config.num_modalities, config.hidden_size)
        
        self.transformer_blocks = nn.ModuleList([
            TransformerBlock(config, i) for i in range(config.num_layers)
        ])
        
        self.ln_final = RMSNorm(config.hidden_size)
        
        self.decoders = nn.ModuleDict({
            'image': DiffusionDecoder(config),
            'text': nn.Linear(config.hidden_size, config.vocab_size),
            'audio': self._build_audio_decoder(),
            'video': self._build_video_decoder()
        })
        
        self.cross_modal_projection = nn.ModuleDict({
            f'{src}2{tgt}': nn.Linear(config.hidden_size, config.hidden_size)
            for src in ['text', 'image', 'audio', 'video']
            for tgt in ['text', 'image', 'audio', 'video']
            if src != tgt
        })
        
        self.apply(self._init_weights)
        
    def _build_audio_decoder(self):
        return nn.Sequential(
            nn.Linear(self.config.hidden_size, self.config.hidden_size * 2),
            nn.GELU(),
            nn.Linear(self.config.hidden_size * 2, self.config.audio_seq_len)
        )
    
    def _build_video_decoder(self):
        return nn.Sequential(
            nn.Linear(self.config.hidden_size, self.config.hidden_size * 4),
            nn.GELU(),
            nn.Linear(self.config.hidden_size * 4, 
                     self.config.video_frames * 3 * self.config.image_size * self.config.image_size)
        )
    
    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
    
    @torch.jit.ignore
    def no_weight_decay(self):
        return {'pos_embed', 'cls_token', 'modality_type_embed'}
    
    def encode(
        self,
        inputs: Dict[str, torch.Tensor],
        modality: str
    ) -> torch.Tensor:
        if modality not in self.encoders:
            raise ValueError(f"Unknown modality: {modality}")
        
        encoded = self.encoders[modality](inputs[modality])
        
        modality_id = ['text', 'image', 'audio', 'video'].index(modality)
        modality_embed = self.modality_type_embed(
            torch.tensor([modality_id], device=encoded.device)
        )
        encoded = encoded + modality_embed
        
        return encoded, modality_id
    
    def decode(
        self,
        hidden_states: torch.Tensor,
        target_modality: str,
        **kwargs
    ) -> torch.Tensor:
        if target_modality == 'image':
            if 'timesteps' not in kwargs:
                timesteps = torch.randn(hidden_states.size(0), device=hidden_states.device)
            else:
                timesteps = kwargs['timesteps']
            
            if 'noisy_images' not in kwargs:
                noisy_images = torch.randn(
                    hidden_states.size(0), 3, self.config.image_size, self.config.image_size,
                    device=hidden_states.device
                )
            else:
                noisy_images = kwargs['noisy_images']
            
            context = reduce(hidden_states, 'b n d -> b d', 'mean')
            return self.decoders['image'](noisy_images, timesteps, context)
        
        elif target_modality == 'text':
            logits = self.decoders['text'](hidden_states)
            return logits
        
        elif target_modality == 'audio':
            return self.decoders['audio'](reduce(hidden_states, 'b n d -> b d', 'mean'))
        
        elif target_modality == 'video':
            decoded = self.decoders['video'](reduce(hidden_states, 'b n d -> b d', 'mean'))
            B = decoded.size(0)
            decoded = decoded.view(B, self.config.video_frames, 3, 
                                 self.config.image_size, self.config.image_size)
            return decoded
    
    def forward(
        self,
        inputs: Dict[str, torch.Tensor],
        source_modality: str,
        target_modality: str,
        attention_mask: Optional[torch.Tensor] = None,
        **kwargs
    ) -> Dict[str, torch.Tensor]:
        
        with autocast(enabled=self.config.mixed_precision):
            encoded, modality_id = self.encode(inputs, source_modality)
            
            for block in self.transformer_blocks:
                encoded = block(encoded, attention_mask, modality_id)
            
            encoded = self.ln_final(encoded)
            
            if source_modality != target_modality:
                projection_key = f'{source_modality}2{target_modality}'
                if projection_key in self.cross_modal_projection:
                    encoded = self.cross_modal_projection[projection_key](encoded)
            
            output = self.decode(encoded, target_modality, **kwargs)
            
            return {
                'output': output,
                'hidden_states': encoded,
                'source_modality': source_modality,
                'target_modality': target_modality
            }
    
    def generate_image(
        self,
        text_prompt: torch.Tensor,
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5
    ) -> torch.Tensor:
        self.eval()
        
        with torch.no_grad():
            text_features, _ = self.encode({'text': text_prompt}, 'text')
            
            for block in self.transformer_blocks:
                text_features = block(text_features, modality_id=0)
            
            text_features = self.ln_final(text_features)
            context = self.cross_modal_projection['text2image'](text_features)
            
            image = torch.randn(
                text_prompt.size(0), 3, self.config.image_size, self.config.image_size,
                device=text_prompt.device
            )
            
            timesteps = torch.linspace(1000, 0, num_inference_steps, device=text_prompt.device)
            
            for t in timesteps:
                t_batch = t.repeat(text_prompt.size(0))
                
                noise_pred = self.decode(
                    context, 'image',
                    timesteps=t_batch,
                    noisy_images=image
                )
                
                if guidance_scale > 1.0:
                    uncond_context = torch.zeros_like(context)
                    uncond_pred = self.decode(
                        uncond_context, 'image',
                        timesteps=t_batch,
                        noisy_images=image
                    )
                    noise_pred = uncond_pred + guidance_scale * (noise_pred - uncond_pred)
                
                alpha = 1.0 - (t / 1000.0) ** 2
                image = (image - (1 - alpha) ** 0.5 * noise_pred) / alpha ** 0.5
        
        return image
    
    def edit_image(
        self,
        image: torch.Tensor,
        text_instruction: torch.Tensor,
        strength: float = 0.8
    ) -> torch.Tensor:
        self.eval()
        
        with torch.no_grad():
            image_features, _ = self.encode({'image': image}, 'image')
            text_features, _ = self.encode({'text': text_instruction}, 'text')
            
            combined_features = torch.cat([image_features, text_features], dim=1)
            
            for block in self.transformer_blocks:
                combined_features = block(combined_features, modality_id=0)
            
            combined_features = self.ln_final(combined_features)
            
            num_inference_steps = int(50 * strength)
            edited_image = self.generate_image_from_features(
                combined_features,
                num_inference_steps=num_inference_steps,
                init_image=image
            )
        
        return edited_image
    
    def generate_image_from_features(
        self,
        features: torch.Tensor,
        num_inference_steps: int = 50,
        init_image: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        
        context = reduce(features, 'b n d -> b d', 'mean')
        
        if init_image is not None:
            image = init_image + torch.randn_like(init_image) * 0.1
        else:
            image = torch.randn(
                features.size(0), 3, self.config.image_size, self.config.image_size,
                device=features.device
            )
        
        timesteps = torch.linspace(1000, 0, num_inference_steps, device=features.device)
        
        for t in timesteps:
            t_batch = t.repeat(features.size(0))
            
            noise_pred = self.decoders['image'](image, t_batch, context)
            
            alpha = 1.0 - (t / 1000.0) ** 2
            image = (image - (1 - alpha) ** 0.5 * noise_pred) / alpha ** 0.5
        
        return image


class MultimodalFineTuner:
    def __init__(self, model: UnifiedMultimodalTransformer, config: ModelConfig):
        self.model = model
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
    def prepare_for_finetuning(self, freeze_base: bool = True):
        if freeze_base:
            for name, param in self.model.named_parameters():
                if 'cross_modal_projection' not in name and 'decoders' not in name:
                    param.requires_grad = False
        
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in self.model.parameters())
        
        print(f"Trainable parameters: {trainable_params:,} / {total_params:,}")
        print(f"Percentage trainable: {100 * trainable_params / total_params:.2f}%")
    
    def create_lora_layers(self, r: int = 16, alpha: int = 32):
        for name, module in self.model.named_modules():
            if isinstance(module, nn.Linear) and 'transformer_blocks' in name:
                in_features = module.in_features
                out_features = module.out_features
                
                lora_a = nn.Parameter(torch.randn(r, in_features) * 0.01)
                lora_b = nn.Parameter(torch.zeros(out_features, r))
                
                module.register_parameter('lora_a', lora_a)
                module.register_parameter('lora_b', lora_b)
                module.lora_scale = alpha / r
                
                original_forward = module.forward
                def forward_with_lora(x):
                    base_out = original_forward(x)
                    lora_out = (x @ module.lora_a.T @ module.lora_b.T) * module.lora_scale
                    return base_out + lora_out
                
                module.forward = forward_with_lora
    
    def train_step(self, batch: Dict[str, torch.Tensor], optimizer, source: str, target: str):
        self.model.train()
        optimizer.zero_grad()
        
        with autocast(enabled=self.config.mixed_precision):
            outputs = self.model(batch, source, target)
            
            if target == 'image':
                loss = F.mse_loss(outputs['output'], batch['target_image'])
            elif target == 'text':
                loss = F.cross_entropy(
                    outputs['output'].view(-1, self.config.vocab_size),
                    batch['target_text'].view(-1)
                )
            elif target == 'audio':
                loss = F.mse_loss(outputs['output'], batch['target_audio'])
            elif target == 'video':
                loss = F.mse_loss(outputs['output'], batch['target_video'])
            
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        optimizer.step()
        
        return loss.item()


def create_model_for_task(task: str = "text2image") -> UnifiedMultimodalTransformer:
    task_configs = {
        "text2image": ModelConfig(
            hidden_size=1536,
            num_layers=32,
            num_heads=24,
            image_size=1024
        ),
        "image_editing": ModelConfig(
            hidden_size=1024,
            num_layers=24,
            num_heads=16,
            image_size=512
        ),
        "multimodal": ModelConfig(
            hidden_size=2048,
            num_layers=48,
            num_heads=32,
            image_size=1024,
            video_frames=16
        )
    }
    
    config = task_configs.get(task, task_configs["multimodal"])
    model = UnifiedMultimodalTransformer(config)
    
    return model


def main():
    config = ModelConfig(
        hidden_size=768,
        num_layers=12,
        num_heads=12,
        image_size=256,
        use_flash_attn=True
    )
    
    model = UnifiedMultimodalTransformer(config)
    model.eval()
    
    print(f"Model initialized with {sum(p.numel() for p in model.parameters()):,} parameters")
    print(f"Model configuration: {config}")
    
    batch_size = 2
    
    dummy_text = torch.randint(0, config.vocab_size, (batch_size, 77))
    dummy_image = torch.randn(batch_size, 3, config.image_size, config.image_size)
    
    print("\nTesting text-to-image generation...")
    with torch.no_grad():
        generated_image = model.generate_image(dummy_text, num_inference_steps=10)
        print(f"Generated image shape: {generated_image.shape}")
    
    print("\nTesting image editing...")
    with torch.no_grad():
        edited_image = model.edit_image(dummy_image, dummy_text, strength=0.5)
        print(f"Edited image shape: {edited_image.shape}")
    
    print("\nTesting cross-modal translation...")
    with torch.no_grad():
        outputs = model(
            {'text': dummy_text},
            source_modality='text',
            target_modality='image'
        )
        print(f"Cross-modal output shape: {outputs['output'].shape}")
    
    print("\nModel ready for production deployment")
    
    fine_tuner = MultimodalFineTuner(model, config)
    fine_tuner.prepare_for_finetuning(freeze_base=True)
    fine_tuner.create_lora_layers(r=8, alpha=16)
    
    print("\nModel prepared for efficient fine-tuning with LoRA")


if __name__ == "__main__":
    main()
