from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "advanced-multimodal-ai"
    service_version: str = "0.5.0"
    environment: str = "development"
    default_runtime_mode: str = "contract"
    default_model_id: str = "adaptive_transformer"
    retrieval_backend: str = "memory"
    qdrant_url: str = "http://vector-db:6333"
    qdrant_collection: str = "multimodal_embeddings"
    retrieval_vector_dim: int = Field(default=8, ge=2, le=4096)
    max_batch_size: int = 8
    max_modalities_per_request: int = 6
    max_vector_results: int = 10
    request_timeout_seconds: float = 20.0
    enable_metrics: bool = True
    rust_core_mode: str = "auto"
    rust_core_binary: str = ""
    async_job_db_path: str = ".runtime/amai_jobs.sqlite3"
    dataset_catalog_db_path: str = ".runtime/amai_catalog.sqlite3"
    connector_db_path: str = ".runtime/amai_connectors.sqlite3"
    drift_baseline_db_path: str = ".runtime/amai_drift.sqlite3"
    pipeline_run_db_path: str = ".runtime/amai_pipelines.sqlite3"
    ontology_db_path: str = ".runtime/amai_ontology.sqlite3"
    recipe_db_path: str = ".runtime/amai_recipes.sqlite3"
    stewardship_db_path: str = ".runtime/amai_stewardship.sqlite3"
    execution_journal_db_path: str = ".runtime/amai_execution_journal.sqlite3"
    repository_theme: str = "signal observatory"
    site_title: str = "Advanced Multi-modal AI"
    default_hidden_dim: int = Field(default=384, ge=64, le=2048)
    stream_event_delay_ms: int = Field(default=30, ge=0, le=2000)
    tensor_intercept_default_mode: str = "observe"
    tensor_intercept_max_risk: float = Field(default=0.74, ge=0.0, le=1.0)
    tensor_intercept_max_entropy: float = Field(default=0.92, ge=0.0, le=1.0)
    tensor_intercept_max_spatial_frequency: float = Field(
        default=0.58,
        ge=0.0,
        le=1.0,
    )
    tensor_intercept_watch_margin: float = Field(default=0.1, ge=0.0, le=0.5)

    model_config = SettingsConfigDict(
        env_prefix="AMAI_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
