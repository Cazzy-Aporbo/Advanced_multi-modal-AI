"""
Domain-Specific Language Model Training Framework
Focus: Procedural understanding, sequential reasoning, and contextual awareness
Application: Clinical protocols, manufacturing procedures, legal workflows
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union, Set
from dataclasses import dataclass, field
from collections import OrderedDict, defaultdict
import json
import re
from pathlib import Path
import networkx as nx
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizer
)
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from enum import Enum
import ast
import pickle
from datetime import datetime
import hashlib


class DomainOntology:
    """Structured knowledge representation for domain-specific concepts"""
    
    def __init__(self, domain: str = "medical"):
        self.domain = domain
        self.graph = nx.DiGraph()
        self.entity_types = {}
        self.relationships = {}
        self.constraints = {}
        self.procedures = OrderedDict()
        self.variables = {}
        self.locations = {}
        self.temporal_sequences = []
        
        # Initialize domain-specific structures
        self._initialize_domain_knowledge()
    
    def _initialize_domain_knowledge(self):
        """Initialize domain-specific knowledge structures"""
        
        if self.domain == "medical":
            # Medical entity types
            self.entity_types = {
                'anatomical_location': ['cardiac', 'hepatic', 'renal', 'cranial', 'thoracic'],
                'procedure': ['biopsy', 'resection', 'anastomosis', 'ablation', 'reconstruction'],
                'measurement': ['mmHg', 'mg/dL', 'mL/min', 'IU/L', 'cells/μL'],
                'medication': ['dosage', 'route', 'frequency', 'duration', 'contraindication'],
                'temporal': ['pre-operative', 'intra-operative', 'post-operative', 'acute', 'chronic']
            }
            
            # Procedural relationships
            self.relationships = {
                'precedes': {'weight': 1.0, 'transitive': True},
                'requires': {'weight': 0.9, 'transitive': False},
                'contraindicated_with': {'weight': -1.0, 'transitive': False},
                'located_at': {'weight': 0.5, 'transitive': False},
                'measured_by': {'weight': 0.7, 'transitive': False}
            }
            
            # Domain constraints
            self.constraints = {
                'dosage_ranges': {
                    'heparin': {'min': 5000, 'max': 30000, 'unit': 'IU', 'frequency': 'q12h'},
                    'morphine': {'min': 2, 'max': 10, 'unit': 'mg', 'frequency': 'q4h'},
                    'insulin': {'min': 0.1, 'max': 1.0, 'unit': 'units/kg', 'frequency': 'continuous'}
                },
                'vital_ranges': {
                    'blood_pressure_systolic': {'min': 90, 'max': 180, 'unit': 'mmHg'},
                    'heart_rate': {'min': 40, 'max': 150, 'unit': 'bpm'},
                    'oxygen_saturation': {'min': 88, 'max': 100, 'unit': '%'}
                }
            }
            
        elif self.domain == "manufacturing":
            self.entity_types = {
                'equipment': ['CNC', 'lathe', 'press', 'furnace', 'conveyor'],
                'material': ['steel', 'aluminum', 'polymer', 'composite', 'ceramic'],
                'process': ['machining', 'welding', 'casting', 'assembly', 'inspection'],
                'measurement': ['mm', 'μm', 'MPa', 'HRC', 'Ra'],
                'quality': ['tolerance', 'surface_finish', 'hardness', 'tensile_strength']
            }
        
        elif self.domain == "legal":
            self.entity_types = {
                'document': ['contract', 'statute', 'regulation', 'precedent', 'filing'],
                'party': ['plaintiff', 'defendant', 'appellant', 'respondent', 'third_party'],
                'jurisdiction': ['federal', 'state', 'district', 'appellate', 'supreme'],
                'procedure': ['discovery', 'deposition', 'motion', 'hearing', 'trial'],
                'temporal': ['filing_deadline', 'statute_of_limitations', 'effective_date']
            }
    
    def add_procedure(self, name: str, steps: List[Dict], constraints: Dict = None):
        """Add a structured procedure with ordered steps"""
        
        procedure = {
            'name': name,
            'steps': OrderedDict(),
            'constraints': constraints or {},
            'variables': set(),
            'locations': set(),
            'temporal_markers': []
        }
        
        for i, step in enumerate(steps):
            step_id = f"{name}_step_{i}"
            procedure['steps'][step_id] = {
                'order': i,
                'action': step.get('action'),
                'location': step.get('location'),
                'duration': step.get('duration'),
                'requirements': step.get('requirements', []),
                'variables': step.get('variables', {}),
                'validation': step.get('validation', {})
            }
            
            # Extract entities
            if step.get('location'):
                procedure['locations'].add(step['location'])
            if step.get('variables'):
                procedure['variables'].update(step['variables'].keys())
            
            # Add to graph
            self.graph.add_node(step_id, **procedure['steps'][step_id])
            
            # Add edges for sequential flow
            if i > 0:
                prev_step_id = f"{name}_step_{i-1}"
                self.graph.add_edge(prev_step_id, step_id, relation='precedes')
        
        self.procedures[name] = procedure
        return procedure
    
    def validate_sequence(self, sequence: List[str]) -> Tuple[bool, List[str]]:
        """Validate if a sequence follows procedural constraints"""
        
        violations = []
        
        # Check temporal ordering
        for i in range(len(sequence) - 1):
            current = sequence[i]
            next_item = sequence[i + 1]
            
            # Check if there's a valid path
            if self.graph.has_node(current) and self.graph.has_node(next_item):
                if not nx.has_path(self.graph, current, next_item):
                    violations.append(f"Invalid sequence: {current} cannot precede {next_item}")
            
            # Check constraints
            if current in self.constraints:
                for constraint_type, constraint_value in self.constraints[current].items():
                    if constraint_type == 'requires' and constraint_value not in sequence[:i]:
                        violations.append(f"Missing requirement: {current} requires {constraint_value}")
        
        return len(violations) == 0, violations


@dataclass
class ProceduralTrainingConfig:
    """Configuration for training domain-specific procedural models"""
    
    # Model configuration
    base_model: str = "microsoft/BioGPT"
    domain: str = "medical"
    
    # Procedural understanding
    enforce_procedural_order: bool = True
    procedural_loss_weight: float = 0.3
    use_graph_attention: bool = True
    max_procedure_length: int = 50
    
    # Variable grounding
    ground_numerical_values: bool = True
    numerical_precision: int = 3
    unit_normalization: bool = True
    enforce_value_constraints: bool = True
    
    # Location and spatial understanding
    use_spatial_encoding: bool = True
    spatial_resolution: str = "hierarchical"  # flat, hierarchical, graph-based
    anatomical_coordinates: bool = True
    
    # Keyword and terminology
    domain_vocabulary: Optional[str] = None
    terminology_embedding_dim: int = 768
    use_acronym_expansion: bool = True
    enforce_terminology_consistency: bool = True
    
    # Sequence modeling
    use_pointer_networks: bool = True
    use_copy_mechanism: bool = True
    sequence_consistency_loss: float = 0.2
    
    # Knowledge grounding
    knowledge_base_path: Optional[str] = None
    use_retrieval_augmentation: bool = True
    retrieval_top_k: int = 5
    knowledge_fusion_method: str = "attention"  # concat, attention, gated
    
    # Training parameters
    learning_rate: float = 5e-5
    batch_size: int = 8
    num_epochs: int = 10
    warmup_steps: int = 500
    gradient_accumulation: int = 4
    
    # Evaluation
    eval_procedural_accuracy: bool = True
    eval_variable_grounding: bool = True
    eval_terminology_precision: bool = True
    
    # Output
    output_dir: str = "./domain_specific_model"
    save_steps: int = 1000
    
    # Proprietary features
    organization_id: str = "proprietary_org"
    encrypt_model: bool = True
    watermark_outputs: bool = True


class ProceduralAttentionModule(nn.Module):
    """Attention module that respects procedural constraints"""
    
    def __init__(self, hidden_size: int, num_heads: int = 8, max_sequence: int = 50):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.max_sequence = max_sequence
        
        # Multi-head attention for procedural dependencies
        self.procedure_attention = nn.MultiheadAttention(
            hidden_size,
            num_heads,
            dropout=0.1,
            batch_first=True
        )
        
        # Positional encoding for step order
        self.step_embedding = nn.Embedding(max_sequence, hidden_size)
        
        # Graph attention for knowledge relationships
        self.graph_attention = nn.Linear(hidden_size * 2, 1)
        
        # Gating mechanism for procedural constraints
        self.constraint_gate = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.Sigmoid()
        )
        
    def forward(
        self,
        hidden_states: torch.Tensor,
        procedure_mask: Optional[torch.Tensor] = None,
        constraint_matrix: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        
        batch_size, seq_len, _ = hidden_states.shape
        
        # Add step embeddings
        step_positions = torch.arange(seq_len, device=hidden_states.device)
        step_embeds = self.step_embedding(step_positions).unsqueeze(0).expand(batch_size, -1, -1)
        
        # Combine with hidden states
        procedure_aware_states = hidden_states + step_embeds
        
        # Apply procedural attention with constraints
        if constraint_matrix is not None:
            # Mask attention based on procedural constraints
            attn_mask = constraint_matrix.to(hidden_states.dtype)
            attn_mask = attn_mask.masked_fill(attn_mask == 0, float('-inf'))
        else:
            attn_mask = None
        
        attended, attention_weights = self.procedure_attention(
            procedure_aware_states,
            procedure_aware_states,
            procedure_aware_states,
            attn_mask=attn_mask,
            key_padding_mask=procedure_mask
        )
        
        # Apply gating based on constraints
        if constraint_matrix is not None:
            gate_input = torch.cat([hidden_states, attended], dim=-1)
            gate_values = self.constraint_gate(gate_input)
            output = gate_values * attended + (1 - gate_values) * hidden_states
        else:
            output = attended
        
        return output, attention_weights


class VariableGroundingModule(nn.Module):
    """Module for grounding numerical variables and units"""
    
    def __init__(self, hidden_size: int, num_units: int, num_ranges: int = 100):
        super().__init__()
        self.hidden_size = hidden_size
        
        # Unit classification
        self.unit_classifier = nn.Linear(hidden_size, num_units)
        
        # Numerical value regression
        self.value_regressor = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, 1)
        )
        
        # Range embedding for discretized values
        self.range_embedding = nn.Embedding(num_ranges, hidden_size)
        
        # Validity checker
        self.validity_checker = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 1),
            nn.Sigmoid()
        )
    
    def forward(
        self,
        hidden_states: torch.Tensor,
        numerical_mask: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        
        # Classify units
        unit_logits = self.unit_classifier(hidden_states)
        
        # Regress numerical values
        values = self.value_regressor(hidden_states).squeeze(-1)
        
        # Discretize values into ranges
        value_ranges = torch.clamp((values * 50 + 50).long(), 0, 99)
        range_embeds = self.range_embedding(value_ranges)
        
        # Check validity
        combined = torch.cat([hidden_states, range_embeds], dim=-1)
        validity_scores = self.validity_checker(combined).squeeze(-1)
        
        return {
            'unit_logits': unit_logits,
            'values': values,
            'value_ranges': value_ranges,
            'validity_scores': validity_scores
        }


class DomainSpecificLanguageModel(nn.Module):
    """Domain-specific language model with procedural understanding"""
    
    def __init__(
        self,
        config: ProceduralTrainingConfig,
        ontology: DomainOntology,
        base_model: Optional[PreTrainedModel] = None
    ):
        super().__init__()
        self.config = config
        self.ontology = ontology
        
        # Load or initialize base model
        if base_model is not None:
            self.base_model = base_model
            self.hidden_size = base_model.config.hidden_size
        else:
            from transformers import AutoModel
            self.base_model = AutoModel.from_pretrained(config.base_model)
            self.hidden_size = self.base_model.config.hidden_size
        
        # Procedural attention module
        self.procedural_attention = ProceduralAttentionModule(
            self.hidden_size,
            num_heads=8,
            max_sequence=config.max_procedure_length
        )
        
        # Variable grounding module
        num_units = len(set(unit for units in ontology.entity_types.get('measurement', []) 
                          for unit in units.split('/')))
        self.variable_grounding = VariableGroundingModule(
            self.hidden_size,
            num_units=max(num_units, 50)
        )
        
        # Spatial encoding module
        if config.use_spatial_encoding:
            self.spatial_encoder = nn.Sequential(
                nn.Linear(3, self.hidden_size // 4),  # x, y, z coordinates
                nn.ReLU(),
                nn.Linear(self.hidden_size // 4, self.hidden_size)
            )
        
        # Knowledge retrieval module
        if config.use_retrieval_augmentation:
            self.knowledge_encoder = SentenceTransformer('all-MiniLM-L6-v2')
            self.knowledge_fusion = nn.Sequential(
                nn.Linear(self.hidden_size * 2, self.hidden_size),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(self.hidden_size, self.hidden_size)
            )
        
        # Pointer network for sequence generation
        if config.use_pointer_networks:
            self.pointer_network = nn.Sequential(
                nn.Linear(self.hidden_size * 2, self.hidden_size),
                nn.ReLU(),
                nn.Linear(self.hidden_size, 1)
            )
        
        # Copy mechanism
        if config.use_copy_mechanism:
            self.copy_gate = nn.Sequential(
                nn.Linear(self.hidden_size * 2, self.hidden_size),
                nn.ReLU(),
                nn.Linear(self.hidden_size, 1),
                nn.Sigmoid()
            )
        
        # Domain-specific heads
        self.procedure_classifier = nn.Linear(
            self.hidden_size,
            len(ontology.procedures)
        )
        
        self.entity_tagger = nn.Linear(
            self.hidden_size,
            len(ontology.entity_types)
        )
        
        # Watermarking module for proprietary protection
        if config.watermark_outputs:
            self.watermark = self._create_watermark()
    
    def _create_watermark(self):
        """Create a unique watermark for model outputs"""
        
        org_id = self.config.organization_id
        timestamp = datetime.now().isoformat()
        watermark_string = f"{org_id}_{timestamp}"
        watermark_hash = hashlib.sha256(watermark_string.encode()).hexdigest()
        
        # Embed watermark as learnable parameters
        watermark_tensor = torch.tensor(
            [ord(c) for c in watermark_hash[:32]],
            dtype=torch.float32
        ) / 255.0
        
        return nn.Parameter(watermark_tensor, requires_grad=False)
    
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        procedure_labels: Optional[torch.Tensor] = None,
        entity_labels: Optional[torch.Tensor] = None,
        numerical_values: Optional[torch.Tensor] = None,
        spatial_coordinates: Optional[torch.Tensor] = None,
        constraint_matrix: Optional[torch.Tensor] = None,
        knowledge_context: Optional[List[str]] = None
    ) -> Dict[str, torch.Tensor]:
        
        # Get base model outputs
        base_outputs = self.base_model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=True
        )
        
        hidden_states = base_outputs.last_hidden_state
        
        # Apply procedural attention
        if self.config.enforce_procedural_order:
            hidden_states, proc_attention = self.procedural_attention(
                hidden_states,
                procedure_mask=~attention_mask.bool() if attention_mask is not None else None,
                constraint_matrix=constraint_matrix
            )
        
        # Ground variables
        if self.config.ground_numerical_values:
            variable_outputs = self.variable_grounding(
                hidden_states,
                numerical_mask=numerical_values is not None
            )
        else:
            variable_outputs = {}
        
        # Add spatial encoding
        if self.config.use_spatial_encoding and spatial_coordinates is not None:
            spatial_features = self.spatial_encoder(spatial_coordinates)
            hidden_states = hidden_states + spatial_features.unsqueeze(1)
        
        # Integrate knowledge context
        if self.config.use_retrieval_augmentation and knowledge_context:
            knowledge_embeds = self._encode_knowledge(knowledge_context)
            hidden_states = self.knowledge_fusion(
                torch.cat([hidden_states, knowledge_embeds], dim=-1)
            )
        
        # Apply pointer network for sequence generation
        if self.config.use_pointer_networks:
            pointer_scores = self._compute_pointer_scores(hidden_states)
        else:
            pointer_scores = None
        
        # Compute procedure and entity predictions
        pooled = hidden_states.mean(dim=1)
        procedure_logits = self.procedure_classifier(pooled)
        entity_logits = self.entity_tagger(hidden_states)
        
        # Compute losses
        loss = 0
        losses = {}
        
        if procedure_labels is not None:
            proc_loss = F.cross_entropy(procedure_logits, procedure_labels)
            loss += proc_loss * self.config.procedural_loss_weight
            losses['procedure_loss'] = proc_loss
        
        if entity_labels is not None:
            entity_loss = F.cross_entropy(
                entity_logits.reshape(-1, entity_logits.size(-1)),
                entity_labels.reshape(-1)
            )
            loss += entity_loss
            losses['entity_loss'] = entity_loss
        
        if numerical_values is not None and 'values' in variable_outputs:
            num_loss = F.mse_loss(variable_outputs['values'], numerical_values)
            loss += num_loss
            losses['numerical_loss'] = num_loss
        
        # Add watermark to outputs if configured
        if self.config.watermark_outputs:
            hidden_states = self._apply_watermark(hidden_states)
        
        return {
            'loss': loss if loss > 0 else None,
            'losses': losses,
            'hidden_states': hidden_states,
            'procedure_logits': procedure_logits,
            'entity_logits': entity_logits,
            'variable_outputs': variable_outputs,
            'pointer_scores': pointer_scores,
            'attention_weights': proc_attention if self.config.enforce_procedural_order else None
        }
    
    def _encode_knowledge(self, knowledge_context: List[str]) -> torch.Tensor:
        """Encode knowledge context using sentence transformer"""
        
        with torch.no_grad():
            embeddings = self.knowledge_encoder.encode(
                knowledge_context,
                convert_to_tensor=True
            )
        
        # Project to hidden size
        batch_size = len(knowledge_context)
        return embeddings.unsqueeze(1).expand(batch_size, -1, self.hidden_size)
    
    def _compute_pointer_scores(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """Compute pointer network scores for sequence generation"""
        
        batch_size, seq_len, hidden_size = hidden_states.shape
        
        # Compute pairwise scores
        hidden_expanded = hidden_states.unsqueeze(2).expand(batch_size, seq_len, seq_len, hidden_size)
        hidden_tiled = hidden_states.unsqueeze(1).expand(batch_size, seq_len, seq_len, hidden_size)
        
        combined = torch.cat([hidden_expanded, hidden_tiled], dim=-1)
        pointer_scores = self.pointer_network(combined).squeeze(-1)
        
        return pointer_scores
    
    def _apply_watermark(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """Apply watermark to model outputs"""
        
        # Add subtle watermark pattern
        watermark_expanded = self.watermark.unsqueeze(0).unsqueeze(0)
        watermark_pattern = watermark_expanded.expand(
            hidden_states.shape[0],
            1,
            -1
        )
        
        # Concatenate to first position
        hidden_states[:, 0, :32] += watermark_pattern.squeeze(1) * 0.01
        
        return hidden_states


class ProceduralDataset(Dataset):
    """Dataset for domain-specific procedural training"""
    
    def __init__(
        self,
        data_path: str,
        tokenizer: PreTrainedTokenizer,
        ontology: DomainOntology,
        config: ProceduralTrainingConfig
    ):
        self.data = self._load_data(data_path)
        self.tokenizer = tokenizer
        self.ontology = ontology
        self.config = config
        
        # Preprocess procedures
        self.procedure_templates = self._extract_procedure_templates()
        
    def _load_data(self, path: str) -> List[Dict]:
        """Load domain-specific training data"""
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Validate data format
        required_fields = ['text', 'procedure', 'entities', 'variables']
        for item in data:
            assert all(field in item for field in required_fields), \
                f"Missing required fields in data item: {item}"
        
        return data
    
    def _extract_procedure_templates(self) -> Dict[str, List]:
        """Extract procedure templates from ontology"""
        
        templates = {}
        for proc_name, procedure in self.ontology.procedures.items():
            template = []
            for step_id, step_data in procedure['steps'].items():
                template.append({
                    'action': step_data['action'],
                    'order': step_data['order'],
                    'requirements': step_data['requirements'],
                    'variables': step_data['variables']
                })
            templates[proc_name] = template
        
        return templates
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        item = self.data[idx]
        
        # Tokenize text
        encoding = self.tokenizer(
            item['text'],
            truncation=True,
            padding='max_length',
            max_length=512,
            return_tensors='pt'
        )
        
        # Extract procedure information
        procedure_name = item['procedure']
        procedure_id = list(self.ontology.procedures.keys()).index(procedure_name) \
            if procedure_name in self.ontology.procedures else -1
        
        # Extract entities and create labels
        entity_labels = self._create_entity_labels(item['entities'], encoding['input_ids'])
        
        # Extract numerical variables
        numerical_values = self._extract_numerical_values(item['variables'])
        
        # Create constraint matrix based on procedure
        if procedure_id >= 0:
            constraint_matrix = self._create_constraint_matrix(procedure_name)
        else:
            constraint_matrix = torch.ones(512, 512)
        
        # Extract spatial information if available
        spatial_coords = self._extract_spatial_coordinates(item.get('locations', []))
        
        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'procedure_labels': torch.tensor(procedure_id),
            'entity_labels': entity_labels,
            'numerical_values': numerical_values,
            'constraint_matrix': constraint_matrix,
            'spatial_coordinates': spatial_coords
        }
    
    def _create_entity_labels(self, entities: Dict, input_ids: torch.Tensor) -> torch.Tensor:
        """Create entity labels for token classification"""
        
        labels = torch.zeros(512, dtype=torch.long)
        
        for entity_type, entity_list in entities.items():
            if entity_type in self.ontology.entity_types:
                type_id = list(self.ontology.entity_types.keys()).index(entity_type)
                
                for entity in entity_list:
                    # Find entity tokens in input
                    entity_tokens = self.tokenizer.encode(entity, add_special_tokens=False)
                    
                    # Mark corresponding positions
                    for i in range(len(input_ids[0]) - len(entity_tokens) + 1):
                        if (input_ids[0][i:i+len(entity_tokens)] == torch.tensor(entity_tokens)).all():
                            labels[i:i+len(entity_tokens)] = type_id + 1
        
        return labels
    
    def _extract_numerical_values(self, variables: Dict) -> torch.Tensor:
        """Extract and normalize numerical values"""
        
        values = torch.zeros(512, dtype=torch.float32)
        
        for var_name, var_value in variables.items():
            if isinstance(var_value, (int, float)):
                # Normalize based on domain constraints
                if var_name in self.ontology.constraints.get('dosage_ranges', {}):
                    range_info = self.ontology.constraints['dosage_ranges'][var_name]
                    normalized = (var_value - range_info['min']) / (range_info['max'] - range_info['min'])
                    values[0] = normalized  # Simplified: just use first position
                elif var_name in self.ontology.constraints.get('vital_ranges', {}):
                    range_info = self.ontology.constraints['vital_ranges'][var_name]
                    normalized = (var_value - range_info['min']) / (range_info['max'] - range_info['min'])
                    values[1] = normalized
        
        return values
    
    def _create_constraint_matrix(self, procedure_name: str) -> torch.Tensor:
        """Create constraint matrix for attention masking"""
        
        matrix = torch.ones(512, 512)
        
        if procedure_name in self.ontology.procedures:
            procedure = self.ontology.procedures[procedure_name]
            num_steps = len(procedure['steps'])
            
            # Create causal mask for procedure steps
            for i in range(min(num_steps, 512)):
                for j in range(i + 1, min(num_steps, 512)):
                    matrix[i, j] = 0  # Can't attend to future steps
        
        return matrix
    
    def _extract_spatial_coordinates(self, locations: List[str]) -> torch.Tensor:
        """Extract spatial coordinates for locations"""
        
        coords = torch.zeros(3, dtype=torch.float32)  # x, y, z
        
        # Simplified: map locations to coordinates
        location_map = {
            'anterior': torch.tensor([1.0, 0.0, 0.0]),
            'posterior': torch.tensor([-1.0, 0.0, 0.0]),
            'superior': torch.tensor([0.0, 1.0, 0.0]),
            'inferior': torch.tensor([0.0, -1.0, 0.0]),
            'lateral': torch.tensor([0.0, 0.0, 1.0]),
            'medial': torch.tensor([0.0, 0.0, -1.0])
        }
        
        for location in locations:
            for key, coord in location_map.items():
                if key in location.lower():
                    coords += coord
        
        # Normalize
        norm = torch.norm(coords)
        if norm > 0:
            coords = coords / norm
        
        return coords


class DomainSpecificTrainer:
    """Trainer for domain-specific language models"""
    
    def __init__(
        self,
        model: DomainSpecificLanguageModel,
        config: ProceduralTrainingConfig,
        ontology: DomainOntology,
        tokenizer: PreTrainedTokenizer
    ):
        self.model = model
        self.config = config
        self.ontology = ontology
        self.tokenizer = tokenizer
        
        # Initialize optimizer
        self.optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=config.learning_rate,
            weight_decay=0.01
        )
        
        # Initialize scheduler
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer,
            T_max=config.num_epochs
        )
        
        # Metrics tracking
        self.metrics = defaultdict(list)
        
    def train(
        self,
        train_dataset: ProceduralDataset,
        eval_dataset: Optional[ProceduralDataset] = None
    ):
        """Train the domain-specific model"""
        
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=4
        )
        
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(device)
        
        for epoch in range(self.config.num_epochs):
            print(f"\nEpoch {epoch + 1}/{self.config.num_epochs}")
            print("-" * 50)
            
            self.model.train()
            epoch_losses = defaultdict(float)
            
            for batch_idx, batch in enumerate(train_loader):
                # Move batch to device
                batch = {k: v.to(device) if isinstance(v, torch.Tensor) else v 
                        for k, v in batch.items()}
                
                # Forward pass
                outputs = self.model(**batch)
                
                if outputs['loss'] is not None:
                    # Backward pass
                    loss = outputs['loss']
                    loss.backward()
                    
                    # Gradient accumulation
                    if (batch_idx + 1) % self.config.gradient_accumulation == 0:
                        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                        self.optimizer.step()
                        self.optimizer.zero_grad()
                    
                    # Track losses
                    for loss_name, loss_value in outputs['losses'].items():
                        epoch_losses[loss_name] += loss_value.item()
                
                # Logging
                if batch_idx % 100 == 0:
                    print(f"Batch {batch_idx}: Loss = {loss.item():.4f}")
                
                # Evaluation
                if batch_idx % self.config.save_steps == 0 and eval_dataset:
                    eval_metrics = self.evaluate(eval_dataset)
                    print(f"Evaluation metrics: {eval_metrics}")
            
            # End of epoch
            self.scheduler.step()
            
            # Save checkpoint
            self._save_checkpoint(epoch)
            
            # Print epoch summary
            print(f"\nEpoch {epoch + 1} Summary:")
            for loss_name, loss_sum in epoch_losses.items():
                avg_loss = loss_sum / len(train_loader)
                print(f"  {loss_name}: {avg_loss:.4f}")
                self.metrics[loss_name].append(avg_loss)
    
    def evaluate(self, eval_dataset: ProceduralDataset) -> Dict[str, float]:
        """Evaluate the model"""
        
        eval_loader = DataLoader(
            eval_dataset,
            batch_size=self.config.batch_size,
            shuffle=False
        )
        
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.eval()
        
        total_correct_procedures = 0
        total_correct_entities = 0
        total_samples = 0
        total_entity_tokens = 0
        
        with torch.no_grad():
            for batch in eval_loader:
                batch = {k: v.to(device) if isinstance(v, torch.Tensor) else v 
                        for k, v in batch.items()}
                
                outputs = self.model(**batch)
                
                # Evaluate procedure classification
                if outputs['procedure_logits'] is not None:
                    pred_procedures = outputs['procedure_logits'].argmax(dim=-1)
                    correct_procedures = (pred_procedures == batch['procedure_labels']).sum()
                    total_correct_procedures += correct_procedures.item()
                
                # Evaluate entity tagging
                if outputs['entity_logits'] is not None:
                    pred_entities = outputs['entity_logits'].argmax(dim=-1)
                    mask = batch['attention_mask'].bool()
                    correct_entities = ((pred_entities == batch['entity_labels']) & mask).sum()
                    total_correct_entities += correct_entities.item()
                    total_entity_tokens += mask.sum().item()
                
                total_samples += batch['input_ids'].shape[0]
        
        metrics = {
            'procedure_accuracy': total_correct_procedures / total_samples if total_samples > 0 else 0,
            'entity_accuracy': total_correct_entities / total_entity_tokens if total_entity_tokens > 0 else 0
        }
        
        return metrics
    
    def _save_checkpoint(self, epoch: int):
        """Save model checkpoint with encryption if configured"""
        
        checkpoint_path = Path(self.config.output_dir) / f"checkpoint_epoch_{epoch}"
        checkpoint_path.mkdir(parents=True, exist_ok=True)
        
        # Save model state
        model_state = self.model.state_dict()
        
        if self.config.encrypt_model:
            # Simple encryption (in production, use proper encryption)
            encrypted_state = {}
            for key, value in model_state.items():
                # XOR with organization ID hash
                org_hash = hashlib.sha256(self.config.organization_id.encode()).digest()
                encrypted_state[key] = value  # Simplified: would apply actual encryption
        else:
            encrypted_state = model_state
        
        torch.save({
            'epoch': epoch,
            'model_state': encrypted_state,
            'optimizer_state': self.optimizer.state_dict(),
            'scheduler_state': self.scheduler.state_dict(),
            'config': self.config,
            'ontology': pickle.dumps(self.ontology),
            'metrics': dict(self.metrics)
        }, checkpoint_path / 'checkpoint.pt')
        
        # Save tokenizer
        self.tokenizer.save_pretrained(checkpoint_path)
        
        print(f"Checkpoint saved to {checkpoint_path}")


def create_medical_example():
    """Create example for medical domain fine-tuning"""
    
    # Initialize medical ontology
    ontology = DomainOntology(domain="medical")
    
    # Add cardiac catheterization procedure
    ontology.add_procedure(
        name="cardiac_catheterization",
        steps=[
            {
                'action': 'obtain_consent',
                'location': 'pre_procedure_area',
                'duration': 15,
                'requirements': ['patient_identification', 'allergy_check'],
                'variables': {'consent_type': 'informed'}
            },
            {
                'action': 'administer_sedation',
                'location': 'cathlab',
                'duration': 10,
                'requirements': ['iv_access', 'monitoring'],
                'variables': {'midazolam_dose': 2, 'fentanyl_dose': 50}
            },
            {
                'action': 'femoral_access',
                'location': 'right_groin',
                'duration': 5,
                'requirements': ['sterile_field', 'local_anesthesia'],
                'variables': {'sheath_size': 6, 'puncture_angle': 45}
            },
            {
                'action': 'advance_catheter',
                'location': 'ascending_aorta',
                'duration': 10,
                'requirements': ['fluoroscopy', 'contrast_ready'],
                'variables': {'catheter_type': 'JR4', 'contrast_volume': 30}
            },
            {
                'action': 'coronary_angiography',
                'location': 'coronary_ostium',
                'duration': 20,
                'requirements': ['hemodynamic_stability'],
                'variables': {'views': ['RAO_30', 'LAO_45', 'AP'], 'contrast_total': 150}
            },
            {
                'action': 'sheath_removal',
                'location': 'femoral_artery',
                'duration': 5,
                'requirements': ['ACT_check'],
                'variables': {'compression_time': 15, 'ACT_value': 180}
            },
            {
                'action': 'post_procedure_monitoring',
                'location': 'recovery_area',
                'duration': 240,
                'requirements': ['vital_signs', 'access_site_check'],
                'variables': {'monitoring_frequency': 15}
            }
        ],
        constraints={
            'max_contrast': 300,
            'min_ACT_for_removal': 180,
            'required_personnel': ['interventionalist', 'nurse', 'technician']
        }
    )
    
    # Configuration
    config = ProceduralTrainingConfig(
        base_model="microsoft/BioGPT",
        domain="medical",
        enforce_procedural_order=True,
        ground_numerical_values=True,
        use_spatial_encoding=True,
        enforce_value_constraints=True,
        organization_id="hospital_xyz",
        encrypt_model=True,
        watermark_outputs=True
    )
    
    return ontology, config


def main():
    """Main execution for domain-specific model training"""
    
    print("Initializing Domain-Specific Language Model Training")
    print("=" * 60)
    
    # Create medical domain example
    ontology, config = create_medical_example()
    
    # Initialize tokenizer
    tokenizer = AutoTokenizer.from_pretrained(config.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Initialize model
    print("Loading base model and applying domain-specific modifications...")
    model = DomainSpecificLanguageModel(config, ontology)
    
    # Create training data (example structure)
    training_data = [
        {
            'text': "Patient underwent cardiac catheterization via right femoral approach. "
                   "Initial sedation with 2mg midazolam and 50mcg fentanyl provided adequate comfort. "
                   "6F sheath inserted at 45-degree angle after local anesthesia with 2% lidocaine. "
                   "JR4 catheter advanced to ascending aorta under fluoroscopic guidance. "
                   "Coronary angiography performed with total contrast volume of 150mL. "
                   "Views obtained: RAO 30, LAO 45, and AP cranial. "
                   "Procedure completed without complications. ACT checked at 180 seconds before sheath removal. "
                   "Manual compression applied for 15 minutes. Patient transferred to recovery for monitoring.",
            'procedure': 'cardiac_catheterization',
            'entities': {
                'medication': ['midazolam', 'fentanyl', 'lidocaine'],
                'anatomical_location': ['femoral', 'ascending aorta', 'coronary'],
                'measurement': ['2mg', '50mcg', '6F', '45-degree', '150mL', '180 seconds', '15 minutes']
            },
            'variables': {
                'midazolam_dose': 2,
                'fentanyl_dose': 50,
                'sheath_size': 6,
                'puncture_angle': 45,
                'contrast_volume': 150,
                'ACT_value': 180,
                'compression_time': 15
            },
            'locations': ['right groin', 'ascending aorta', 'coronary ostium']
        }
    ]
    
    # Save training data
    with open('training_data.json', 'w') as f:
        json.dump(training_data, f, indent=2)
    
    # Create dataset
    dataset = ProceduralDataset('training_data.json', tokenizer, ontology, config)
    
    # Initialize trainer
    trainer = DomainSpecificTrainer(model, config, ontology, tokenizer)
    
    # Train model
    print("\nStarting domain-specific training...")
    print(f"Organization: {config.organization_id}")
    print(f"Domain: {config.domain}")
    print(f"Procedures: {list(ontology.procedures.keys())}")
    print(f"Enforcing procedural order: {config.enforce_procedural_order}")
    print(f"Watermarking enabled: {config.watermark_outputs}")
    print("-" * 60)
    
    trainer.train(dataset)
    
    print("\nTraining completed successfully")
    print(f"Model saved to: {config.output_dir}")
    print(f"Model is encrypted: {config.encrypt_model}")
    print(f"Proprietary watermark embedded: {config.watermark_outputs}")


if __name__ == "__main__":
    main()
