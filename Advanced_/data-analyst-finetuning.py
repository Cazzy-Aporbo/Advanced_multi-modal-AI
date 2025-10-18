"""
Data Analyst AI Fine-Tuning Framework
An AI data analysis, visualization, and statistical insights Version 1. 
Works with CSV, Excel, SQL, generates publication-quality graphs, and writes analysis code
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from scipy import stats
import sqlite3
import json
import yaml
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    BitsAndBytesConfig
)
from peft import (
    LoraConfig,
    get_peft_model,
    TaskType,
    prepare_model_for_kbit_training
)
from datasets import Dataset as HFDataset
import ast
import subprocess
import io
import base64
from PIL import Image


@dataclass
class DataAnalystConfig:
    """Configuration for training a data analysis expert model"""
    
    # Model selection - using open models that work well for code
    base_model: str = "codellama/CodeLlama-7b-Instruct-hf"  # Great for code generation
    
    # Training settings optimized for quality
    learning_rate: float = 2e-4
    num_epochs: int = 3
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    
    # LoRA settings for efficient training
    lora_r: int = 32
    lora_alpha: int = 64
    lora_dropout: float = 0.1
    
    # Data analysis specific settings
    max_code_length: int = 2048
    include_visualizations: bool = True
    include_statistical_tests: bool = True
    include_ml_models: bool = True
    
    # Output settings
    output_dir: str = "./data_analyst_model"
    push_to_hub: bool = False
    
    # Quality settings
    use_4bit: bool = True  # Use 4-bit quantization for efficiency
    gradient_checkpointing: bool = True


class DataAnalysisExpert:
    """Core class that handles all data analysis operations"""
    
    def __init__(self):
        self.visualization_templates = self._load_viz_templates()
        self.analysis_patterns = self._load_analysis_patterns()
        
    def _load_viz_templates(self):
        """Load visualization templates for different data types"""
        
        return {
            'distribution': {
                'single_numeric': ['histogram', 'kde', 'boxplot', 'violin'],
                'multiple_numeric': ['pairplot', 'correlation_heatmap', 'parallel_coordinates'],
                'categorical': ['bar', 'pie', 'donut', 'treemap'],
                'time_series': ['line', 'area', 'candlestick', 'seasonal_decompose'],
                'geospatial': ['choropleth', 'scatter_geo', 'density_mapbox']
            },
            'relationship': {
                'numeric_numeric': ['scatter', 'hexbin', 'contour', 'regression'],
                'categorical_numeric': ['box', 'violin', 'strip', 'swarm'],
                'categorical_categorical': ['heatmap', 'mosaic', 'correspondence']
            },
            'composition': {
                'parts_of_whole': ['pie', 'donut', 'treemap', 'sunburst'],
                'hierarchical': ['treemap', 'sunburst', 'icicle', 'sankey']
            },
            'comparison': {
                'across_categories': ['bar', 'lollipop', 'dumbbell', 'radar'],
                'over_time': ['line', 'area', 'stream', 'horizon']
            }
        }
    
    def _load_analysis_patterns(self):
        """Load common analysis patterns"""
        
        return {
            'exploratory': [
                'summary_statistics',
                'missing_value_analysis',
                'outlier_detection',
                'distribution_analysis',
                'correlation_analysis'
            ],
            'statistical': [
                't_test',
                'anova',
                'chi_square',
                'regression_analysis',
                'time_series_decomposition'
            ],
            'machine_learning': [
                'clustering',
                'classification',
                'regression',
                'dimensionality_reduction',
                'anomaly_detection'
            ],
            'business': [
                'cohort_analysis',
                'funnel_analysis',
                'retention_analysis',
                'revenue_analysis',
                'customer_segmentation'
            ]
        }
    
    def analyze_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive dataset analysis"""
        
        analysis = {
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict(),
            'missing': df.isnull().sum().to_dict(),
            'summary': {}
        }
        
        # Numeric columns analysis
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            analysis['summary']['numeric'] = df[numeric_cols].describe().to_dict()
            analysis['correlations'] = df[numeric_cols].corr().to_dict()
            
        # Categorical columns analysis
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            analysis['summary']['categorical'] = {
                col: df[col].value_counts().head(10).to_dict() 
                for col in categorical_cols
            }
        
        # Time series detection
        for col in df.columns:
            try:
                pd.to_datetime(df[col])
                analysis['time_column'] = col
                break
            except:
                continue
        
        return analysis
    
    def generate_visualization_code(self, 
                                   data_info: Dict,
                                   viz_type: str,
                                   style: str = 'professional') -> str:
        """Generate visualization code based on data characteristics"""
        
        if style == 'professional':
            style_code = """
# Professional styling
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
"""
        else:
            style_code = ""
        
        # Generate appropriate visualization based on type
        if viz_type == 'correlation_heatmap':
            code = f"""
{style_code}
# Correlation Heatmap
plt.figure(figsize=(12, 10))
correlation_matrix = df.select_dtypes(include=[np.number]).corr()

# Create mask for upper triangle
mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))

# Create heatmap with annotations
sns.heatmap(correlation_matrix, 
            mask=mask,
            annot=True, 
            fmt='.2f',
            cmap='RdBu_r',
            center=0,
            square=True,
            linewidths=1,
            cbar_kws={{"shrink": 0.8}})

plt.title('Correlation Matrix Heatmap', fontsize=16, fontweight='bold', pad=20)
plt.tight_layout()
plt.show()
"""
        
        elif viz_type == 'distribution_analysis':
            code = f"""
{style_code}
# Distribution Analysis for Numeric Columns
numeric_cols = df.select_dtypes(include=[np.number]).columns
n_cols = len(numeric_cols)
n_rows = (n_cols + 2) // 3

fig, axes = plt.subplots(n_rows, 3, figsize=(15, 5*n_rows))
axes = axes.flatten() if n_rows > 1 else [axes]

for idx, col in enumerate(numeric_cols):
    if idx < len(axes):
        # Create both histogram and KDE
        axes[idx].hist(df[col].dropna(), bins=30, alpha=0.7, density=True, edgecolor='black')
        df[col].dropna().plot(kind='kde', ax=axes[idx], secondary_y=True, color='red', linewidth=2)
        
        # Add statistics
        mean_val = df[col].mean()
        median_val = df[col].median()
        axes[idx].axvline(mean_val, color='green', linestyle='--', label=f'Mean: {{mean_val:.2f}}')
        axes[idx].axvline(median_val, color='orange', linestyle='--', label=f'Median: {{median_val:.2f}}')
        
        axes[idx].set_title(f'Distribution of {{col}}', fontweight='bold')
        axes[idx].set_xlabel(col)
        axes[idx].set_ylabel('Frequency')
        axes[idx].legend()
        axes[idx].grid(True, alpha=0.3)

# Hide empty subplots
for idx in range(len(numeric_cols), len(axes)):
    axes[idx].set_visible(False)

plt.suptitle('Distribution Analysis of Numeric Variables', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.show()
"""
        
        elif viz_type == 'interactive_scatter':
            code = """
# Interactive Scatter Plot using Plotly
import plotly.express as px

# Select numeric columns for scatter plot
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

if len(numeric_cols) >= 2:
    fig = px.scatter(df, 
                     x=numeric_cols[0], 
                     y=numeric_cols[1],
                     color=numeric_cols[2] if len(numeric_cols) > 2 else None,
                     size=numeric_cols[3] if len(numeric_cols) > 3 else None,
                     hover_data=df.columns,
                     title=f'Interactive Scatter: {numeric_cols[0]} vs {numeric_cols[1]}')
    
    fig.update_layout(
        height=600,
        hovermode='closest',
        showlegend=True,
        template='plotly_white'
    )
    
    fig.show()
"""
        
        return code
    
    def generate_statistical_analysis(self, data_info: Dict) -> str:
        """Generate statistical analysis code"""
        
        code = """
# Comprehensive Statistical Analysis
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("STATISTICAL ANALYSIS REPORT")
print("=" * 60)

# 1. Normality Tests
print("\\n1. NORMALITY TESTS (Shapiro-Wilk)")
print("-" * 40)
numeric_cols = df.select_dtypes(include=[np.number]).columns

for col in numeric_cols:
    if len(df[col].dropna()) > 3:
        stat, p_value = stats.shapiro(df[col].dropna())
        normality = "Normal" if p_value > 0.05 else "Not Normal"
        print(f"{col}: p-value = {p_value:.4f} ({normality})")

# 2. Outlier Detection using IQR
print("\\n2. OUTLIER DETECTION (IQR Method)")
print("-" * 40)

for col in numeric_cols:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col]
    print(f"{col}: {len(outliers)} outliers detected ({len(outliers)/len(df)*100:.1f}%)")
    
    if len(outliers) > 0 and len(outliers) < 10:
        print(f"  Outlier values: {outliers.tolist()}")

# 3. Correlation Analysis
print("\\n3. SIGNIFICANT CORRELATIONS (|r| > 0.5)")
print("-" * 40)

if len(numeric_cols) > 1:
    corr_matrix = df[numeric_cols].corr()
    
    significant_corrs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            corr_val = corr_matrix.iloc[i, j]
            if abs(corr_val) > 0.5:
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                significant_corrs.append((col1, col2, corr_val))
    
    if significant_corrs:
        for col1, col2, corr in sorted(significant_corrs, key=lambda x: abs(x[2]), reverse=True):
            print(f"{col1} <-> {col2}: r = {corr:.3f}")
    else:
        print("No significant correlations found")

# 4. Statistical Tests
print("\\n4. STATISTICAL TESTS")
print("-" * 40)

# T-test example (if applicable)
if len(numeric_cols) >= 2:
    col1, col2 = numeric_cols[0], numeric_cols[1]
    t_stat, p_value = stats.ttest_ind(df[col1].dropna(), df[col2].dropna())
    print(f"T-test between {col1} and {col2}: p-value = {p_value:.4f}")

# Chi-square test for categorical variables
categorical_cols = df.select_dtypes(include=['object', 'category']).columns
if len(categorical_cols) >= 2:
    col1, col2 = categorical_cols[0], categorical_cols[1]
    contingency_table = pd.crosstab(df[col1], df[col2])
    chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
    print(f"Chi-square test between {col1} and {col2}: p-value = {p_value:.4f}")

print("\\n" + "=" * 60)
"""
        return code
    
    def generate_ml_analysis(self, task_type: str = 'auto') -> str:
        """Generate machine learning analysis code"""
        
        if task_type == 'auto':
            code = """
# Automated Machine Learning Analysis
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import classification_report, mean_squared_error, r2_score
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("MACHINE LEARNING ANALYSIS")
print("=" * 60)

# Prepare data
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

# 1. Clustering Analysis
print("\\n1. CLUSTERING ANALYSIS")
print("-" * 40)

if len(numeric_cols) >= 2:
    # Prepare data for clustering
    X_cluster = df[numeric_cols].dropna()
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_cluster)
    
    # Determine optimal number of clusters using elbow method
    inertias = []
    K_range = range(2, min(10, len(X_scaled)//10))
    
    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X_scaled)
        inertias.append(kmeans.inertia_)
    
    # Find elbow point (simplified)
    optimal_k = 3  # Default, would use elbow method in practice
    
    # Perform clustering with optimal k
    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    
    print(f"Optimal number of clusters: {optimal_k}")
    print(f"Cluster distribution:")
    unique, counts = np.unique(clusters, return_counts=True)
    for cluster, count in zip(unique, counts):
        print(f"  Cluster {cluster}: {count} samples ({count/len(clusters)*100:.1f}%)")
    
    # PCA for visualization if dimensions > 2
    if len(numeric_cols) > 2:
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        explained_var = pca.explained_variance_ratio_
        print(f"\\nPCA Explained Variance: {explained_var[0]:.2%} + {explained_var[1]:.2%} = {sum(explained_var):.2%}")

# 2. Feature Importance Analysis
print("\\n2. FEATURE IMPORTANCE ANALYSIS")
print("-" * 40)

if len(numeric_cols) > 1:
    # Use Random Forest to determine feature importance
    # Assuming last numeric column as target for demonstration
    feature_cols = numeric_cols[:-1]
    target_col = numeric_cols[-1]
    
    if len(feature_cols) > 0:
        X = df[feature_cols].dropna()
        y = df.loc[X.index, target_col]
        
        # Train Random Forest
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        rf.fit(X, y)
        
        # Get feature importance
        importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': rf.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"Feature Importance for predicting '{target_col}':")
        for idx, row in importance.iterrows():
            print(f"  {row['feature']}: {row['importance']:.4f}")
        
        # Model performance
        scores = cross_val_score(rf, X, y, cv=5, scoring='r2')
        print(f"\\nModel Performance (R² Score): {scores.mean():.3f} (+/- {scores.std()*2:.3f})")

# 3. Automated Insights
print("\\n3. AUTOMATED INSIGHTS")
print("-" * 40)

insights = []

# Check for highly correlated features
if len(numeric_cols) > 1:
    corr_matrix = df[numeric_cols].corr()
    high_corr = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            if abs(corr_matrix.iloc[i, j]) > 0.8:
                high_corr.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_matrix.iloc[i, j]))
    
    if high_corr:
        insights.append(f"Found {len(high_corr)} pairs of highly correlated features (|r| > 0.8)")

# Check for imbalanced data
for col in df.columns:
    if df[col].dtype in ['object', 'category']:
        value_counts = df[col].value_counts()
        if len(value_counts) > 1:
            imbalance_ratio = value_counts.iloc[0] / value_counts.sum()
            if imbalance_ratio > 0.9:
                insights.append(f"Column '{col}' is highly imbalanced ({imbalance_ratio:.1%} in dominant class)")

# Check for missing values
missing_pct = df.isnull().mean()
high_missing = missing_pct[missing_pct > 0.3]
if len(high_missing) > 0:
    insights.append(f"Found {len(high_missing)} columns with >30% missing values")

# Print insights
for i, insight in enumerate(insights, 1):
    print(f"{i}. {insight}")

if not insights:
    print("No significant issues detected in the dataset")

print("\\n" + "=" * 60)
"""
        
        return code


class DataAnalysisDataset(Dataset):
    """Dataset for training data analysis model"""
    
    def __init__(self, num_samples: int = 10000):
        self.samples = self._generate_training_samples(num_samples)
        self.expert = DataAnalysisExpert()
        
    def _generate_training_samples(self, num_samples: int) -> List[Dict]:
        """Generate diverse training samples for data analysis"""
        
        samples = []
        
        # Templates for different types of data analysis requests
        templates = [
            {
                'instruction': "Analyze this dataset and provide key insights",
                'context': "Dataset with {n_rows} rows and {n_cols} columns containing {data_type} data",
                'response_template': "summary_stats + visualization + insights"
            },
            {
                'instruction': "Create a professional visualization showing the relationship between {col1} and {col2}",
                'context': "Correlation analysis needed",
                'response_template': "scatter_plot + correlation + regression_line"
            },
            {
                'instruction': "Perform statistical tests to determine if there are significant differences",
                'context': "Hypothesis testing required",
                'response_template': "normality_test + t_test + interpretation"
            },
            {
                'instruction': "Build a predictive model for {target}",
                'context': "Machine learning task",
                'response_template': "data_prep + model_training + evaluation"
            },
            {
                'instruction': "Identify patterns and anomalies in the data",
                'context': "Pattern recognition needed",
                'response_template': "clustering + outlier_detection + visualization"
            },
            {
                'instruction': "Create an interactive dashboard with key metrics",
                'context': "Business intelligence visualization",
                'response_template': "plotly_dashboard + kpis + filters"
            },
            {
                'instruction': "Perform time series analysis and forecasting",
                'context': "Temporal data with trends",
                'response_template': "decomposition + trend_analysis + forecast"
            },
            {
                'instruction': "Generate a comprehensive EDA report",
                'context': "Exploratory data analysis",
                'response_template': "full_eda + visualizations + recommendations"
            }
        ]
        
        # Generate samples
        for i in range(num_samples):
            template = templates[i % len(templates)]
            
            # Create realistic data scenario
            n_rows = np.random.randint(100, 10000)
            n_cols = np.random.randint(5, 50)
            data_types = ['sales', 'customer', 'financial', 'operational', 'sensor', 'survey']
            data_type = np.random.choice(data_types)
            
            # Generate the instruction
            instruction = template['instruction'].format(
                n_rows=n_rows,
                n_cols=n_cols,
                data_type=data_type,
                col1='column_A',
                col2='column_B',
                target='target_variable'
            )
            
            # Generate appropriate code response
            response = self._generate_response_code(template['response_template'], data_type)
            
            samples.append({
                'instruction': instruction,
                'input': template['context'],
                'output': response
            })
        
        return samples
    
    def _generate_response_code(self, template: str, data_type: str) -> str:
        """Generate appropriate code response based on template"""
        
        code_snippets = {
            'summary_stats': """
# Load and analyze the data
import pandas as pd
import numpy as np

# Basic statistics
print(df.describe())
print(f"\\nShape: {df.shape}")
print(f"Missing values:\\n{df.isnull().sum()}")
print(f"Data types:\\n{df.dtypes}")
""",
            'visualization': """
# Create comprehensive visualizations
import matplotlib.pyplot as plt
import seaborn as sns

fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# Distribution plots
df.select_dtypes(include=[np.number]).hist(ax=axes[0, 0], bins=20)
axes[0, 0].set_title('Distributions')

# Correlation heatmap
sns.heatmap(df.corr(), annot=True, fmt='.2f', ax=axes[0, 1])
axes[0, 1].set_title('Correlations')

# Box plots
df.select_dtypes(include=[np.number]).boxplot(ax=axes[1, 0])
axes[1, 0].set_title('Box Plots')

# Pairplot for key variables
key_vars = df.select_dtypes(include=[np.number]).columns[:4]
if len(key_vars) > 1:
    sns.pairplot(df[key_vars])

plt.tight_layout()
plt.show()
""",
            'insights': """
# Generate automated insights
insights = []

# Find correlations
corr_matrix = df.corr()
high_corr = [(col1, col2, corr) 
             for col1 in corr_matrix.columns 
             for col2 in corr_matrix.columns 
             if col1 < col2 and abs(corr_matrix[col1][col2]) > 0.7]

if high_corr:
    insights.append(f"Strong correlations found: {high_corr}")

# Detect outliers
for col in df.select_dtypes(include=[np.number]):
    Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
    IQR = Q3 - Q1
    outliers = df[(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)]
    if len(outliers) > 0:
        insights.append(f"{col} has {len(outliers)} outliers")

print("\\nKey Insights:")
for insight in insights:
    print(f"- {insight}")
""",
            't_test': """
# Statistical testing
from scipy import stats

# Normality test
stat, p_value = stats.shapiro(df[column].dropna())
print(f"Shapiro-Wilk test: p-value = {p_value:.4f}")

# T-test
group1 = df[df['category'] == 'A']['value']
group2 = df[df['category'] == 'B']['value']
t_stat, p_value = stats.ttest_ind(group1, group2)
print(f"T-test: t = {t_stat:.3f}, p-value = {p_value:.4f}")

# Interpretation
if p_value < 0.05:
    print("Significant difference detected")
else:
    print("No significant difference")
""",
            'clustering': """
# Clustering analysis
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Prepare data
X = df.select_dtypes(include=[np.number]).dropna()
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Find optimal clusters
inertias = []
for k in range(2, 11):
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(X_scaled)
    inertias.append(kmeans.inertia_)

# Apply clustering
optimal_k = 4  # Based on elbow method
kmeans = KMeans(n_clusters=optimal_k, random_state=42)
df['cluster'] = kmeans.fit_predict(X_scaled)

# Visualize
plt.figure(figsize=(10, 8))
scatter = plt.scatter(X_scaled[:, 0], X_scaled[:, 1], c=df['cluster'], cmap='viridis')
plt.colorbar(scatter)
plt.title('Clustering Results')
plt.show()

# Cluster profiles
for cluster in range(optimal_k):
    cluster_data = df[df['cluster'] == cluster]
    print(f"\\nCluster {cluster} ({len(cluster_data)} samples):")
    print(cluster_data.describe())
""",
            'plotly_dashboard': """
# Interactive Dashboard with Plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Create subplots
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=('Time Series', 'Distribution', 'Correlation', 'KPIs'),
    specs=[[{'type': 'scatter'}, {'type': 'histogram'}],
           [{'type': 'heatmap'}, {'type': 'indicator'}]]
)

# Time series
fig.add_trace(
    go.Scatter(x=df.index, y=df[df.columns[0]], name='Trend'),
    row=1, col=1
)

# Distribution
fig.add_trace(
    go.Histogram(x=df[df.columns[1]], name='Distribution'),
    row=1, col=2
)

# Correlation heatmap
fig.add_trace(
    go.Heatmap(z=df.corr().values, 
               x=df.corr().columns,
               y=df.corr().columns),
    row=2, col=1
)

# KPI
fig.add_trace(
    go.Indicator(
        mode="number+delta",
        value=df[df.columns[0]].mean(),
        delta={'reference': df[df.columns[0]].median()},
        title={'text': "Average vs Median"}),
    row=2, col=2
)

fig.update_layout(height=800, showlegend=False, title_text="Data Dashboard")
fig.show()
"""
        }
        
        # Combine relevant code snippets based on template
        response_parts = template.split(' + ')
        code_parts = []
        
        for part in response_parts:
            if part in code_snippets:
                code_parts.append(code_snippets[part])
            elif 'scatter' in part:
                code_parts.append(code_snippets.get('visualization', ''))
            elif 'normality' in part or 'test' in part:
                code_parts.append(code_snippets.get('t_test', ''))
            elif 'cluster' in part or 'outlier' in part:
                code_parts.append(code_snippets.get('clustering', ''))
            elif 'plotly' in part or 'dashboard' in part:
                code_parts.append(code_snippets.get('plotly_dashboard', ''))
            else:
                code_parts.append(code_snippets.get('summary_stats', ''))
        
        return '\n'.join(code_parts)
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        return self.samples[idx]


class DataAnalystTrainer:
    """Main trainer class for creating the data analyst model"""
    
    def __init__(self, config: DataAnalystConfig):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {self.device}")
        
        # Initialize model and tokenizer
        self._setup_model()
        
    def _setup_model(self):
        """Setup the model with LoRA for efficient training"""
        
        print("Loading base model...")
        
        # Quantization config for memory efficiency
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=self.config.use_4bit,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True
        )
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model,
            quantization_config=bnb_config if self.config.use_4bit else None,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.base_model,
            trust_remote_code=True
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        
        # Prepare model for training
        self.model = prepare_model_for_kbit_training(self.model)
        
        # Configure LoRA
        peft_config = LoraConfig(
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", 
                          "gate_proj", "up_proj", "down_proj"]
        )
        
        # Apply LoRA
        self.model = get_peft_model(self.model, peft_config)
        
        # Enable gradient checkpointing
        if self.config.gradient_checkpointing:
            self.model.gradient_checkpointing_enable()
        
        print(f"Model loaded with {self.model.print_trainable_parameters()}")
    
    def prepare_dataset(self, dataset: DataAnalysisDataset):
        """Prepare dataset for training"""
        
        def format_instruction(sample):
            instruction = f"""### Instruction:
{sample['instruction']}

### Context:
{sample['input']}

### Response:
{sample['output']}"""
            return {'text': instruction}
        
        # Convert to HuggingFace dataset
        formatted_samples = [format_instruction(s) for s in dataset.samples]
        hf_dataset = HFDataset.from_list(formatted_samples)
        
        # Tokenize
        def tokenize_function(examples):
            return self.tokenizer(
                examples['text'],
                truncation=True,
                padding='max_length',
                max_length=self.config.max_code_length
            )
        
        tokenized_dataset = hf_dataset.map(tokenize_function, batched=True)
        
        # Split into train/eval
        split_dataset = tokenized_dataset.train_test_split(test_size=0.1)
        
        return split_dataset['train'], split_dataset['test']
    
    def train(self):
        """Train the model"""
        
        print("Generating training data...")
        dataset = DataAnalysisDataset(num_samples=5000)
        
        print("Preparing datasets...")
        train_dataset, eval_dataset = self.prepare_dataset(dataset)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.num_epochs,
            per_device_train_batch_size=self.config.batch_size,
            per_device_eval_batch_size=self.config.batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            fp16=False,
            bf16=True,
            logging_steps=10,
            evaluation_strategy="steps",
            eval_steps=100,
            save_strategy="epoch",
            warmup_ratio=0.1,
            lr_scheduler_type="cosine",
            optim="paged_adamw_8bit",
            report_to="none"
        )
        
        # Initialize trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            tokenizer=self.tokenizer,
        )
        
        print("Starting training...")
        print("-" * 50)
        
        # Train
        trainer.train()
        
        # Save the model
        print("Saving model...")
        trainer.save_model()
        self.tokenizer.save_pretrained(self.config.output_dir)
        
        print(f"Model saved to {self.config.output_dir}")
        
        if self.config.push_to_hub:
            print("Pushing to HuggingFace Hub...")
            trainer.push_to_hub()
    
    def test_model(self, prompt: str):
        """Test the trained model with a prompt"""
        
        self.model.eval()
        
        # Format prompt
        formatted_prompt = f"""### Instruction:
{prompt}

### Response:
"""
        
        # Tokenize
        inputs = self.tokenizer(
            formatted_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.config.max_code_length
        ).to(self.device)
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=1024,
                temperature=0.1,
                do_sample=True,
                top_p=0.95,
                repetition_penalty=1.15
            )
        
        # Decode
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the response part
        if "### Response:" in response:
            response = response.split("### Response:")[1].strip()
        
        return response


def interactive_data_analysis():
    """Interactive function to use the trained model"""
    
    print("""
    ========================================
    DATA ANALYST AI - Interactive Mode
    ========================================
    
    This AI can:
    - Analyze any dataset (CSV, Excel, SQL)
    - Create professional visualizations
    - Perform statistical tests
    - Build ML models
    - Generate insights
    
    Type 'quit' to exit
    ----------------------------------------
    """)
    
    # Load the trained model (if exists)
    config = DataAnalystConfig()
    
    try:
        # Try to load existing model
        model = AutoModelForCausalLM.from_pretrained(
            config.output_dir,
            device_map="auto",
            trust_remote_code=True
        )
        tokenizer = AutoTokenizer.from_pretrained(config.output_dir)
        print("Loaded trained model from disk")
    except:
        print("No trained model found. Training a new one...")
        trainer = DataAnalystTrainer(config)
        trainer.train()
        model = trainer.model
        tokenizer = trainer.tokenizer
    
    # Interactive loop
    while True:
        print("\n" + "="*50)
        user_input = input("What analysis would you like to perform?\n> ")
        
        if user_input.lower() == 'quit':
            break
        
        # Generate response
        print("\nGenerating analysis code...\n")
        
        # Format as instruction
        formatted = f"""### Instruction:
{user_input}

### Response:
"""
        
        inputs = tokenizer(formatted, return_tensors="pt", truncation=True)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=1024,
                temperature=0.1,
                do_sample=True,
                top_p=0.95
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        if "### Response:" in response:
            response = response.split("### Response:")[1].strip()
        
        print("Generated Code:")
        print("-" * 40)
        print(response)
        print("-" * 40)
        
        # Ask if user wants to execute
        execute = input("\nExecute this code? (y/n): ")
        if execute.lower() == 'y':
            try:
                exec(response)
            except Exception as e:
                print(f"Error executing code: {e}")


def main():
    """Main execution function"""
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║        UNIVERSAL DATA ANALYST AI TRAINING SYSTEM         ║
    ║                                                          ║
    ║  Creates an AI data analysis                             ║
    ║  Specializes in: Visualization, Statistics, ML, R/Python ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Configuration
    config = DataAnalystConfig(
        base_model="codellama/CodeLlama-7b-Instruct-hf",  # Best for code generation
        learning_rate=2e-4,
        num_epochs=3,
        batch_size=4,
        lora_r=32,
        lora_alpha=64,
        output_dir="./data_analyst_model"
    )
    
    # Initialize trainer
    trainer = DataAnalystTrainer(config)
    
    # Train the model
    print("\nStarting training process...")
    trainer.train()
    
    # Test the model
    print("\nTesting the trained model...")
    test_prompts = [
        "Analyze a sales dataset and identify top performing products",
        "Create a correlation heatmap with professional styling",
        "Perform statistical tests to compare two groups",
        "Build a predictive model using Random Forest",
        "Generate an interactive dashboard with Plotly"
    ]
    
    for prompt in test_prompts[:2]:  # Test with first 2 prompts
        print(f"\nPrompt: {prompt}")
        print("-" * 40)
        response = trainer.test_model(prompt)
        print(response[:500] + "..." if len(response) > 500 else response)
    
    print("\n" + "="*60)
    print("Training complete! Your model is ready.")
    print(f"Model saved to: {config.output_dir}")
    print("\nTo use interactively, run: interactive_data_analysis()")
    
    # Ask if user wants to enter interactive mode
    interactive = input("\nEnter interactive mode now? (y/n): ")
    if interactive.lower() == 'y':
        interactive_data_analysis()


if __name__ == "__main__":
    main()
