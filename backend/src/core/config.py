"""Configuration loader for the application."""
import os
import yaml
from pathlib import Path
from typing import Any, Dict
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ScrapingConfig(BaseModel):
    """Scraping configuration."""
    interval_minutes: int
    keywords: list[str]
    delays: Dict[str, int]


class AIConfig(BaseModel):
    """AI configuration."""
    provider: str
    api_key: str
    daily_limit: int
    input_max_chars: int
    models: Dict[str, str]


class ClusteringConfig(BaseModel):
    """Clustering configuration."""
    embedding_similarity_threshold: float
    time_window_hours: int


class ContentConfig(BaseModel):
    """Content configuration."""
    archive_after_hours: int
    retention_days: int
    hotness_threshold: int


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    probe_interval_minutes: int
    failure_alert_threshold: int
    degradation_threshold: int
    admin_email: str


class PushConfig(BaseModel):
    """Push notification configuration."""
    polling_interval_seconds: int


class DryRunConfig(BaseModel):
    """Dry-run mode configuration."""
    enabled: bool = False


class Config(BaseSettings):
    """Application configuration."""
    scraping: ScrapingConfig
    ai: AIConfig
    clustering: ClusteringConfig
    content: ContentConfig
    monitoring: MonitoringConfig
    push: PushConfig
    dry_run: DryRunConfig

    # Environment variables
    aliyun_api_key: str = Field(default="", alias="ALIYUN_API_KEY")
    admin_email: str = Field(default="", alias="ADMIN_EMAIL")
    smtp_server: str = Field(default="", alias="SMTP_SERVER")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    bing_search_api_key: str = Field(default="", alias="BING_SEARCH_API_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


def load_config(config_path: str = "config.yaml") -> Config:
    """
    Load configuration from YAML file and environment variables.

    Args:
        config_path: Path to config.yaml file

    Returns:
        Config object with all settings
    """
    # Load YAML config
    config_file = Path(__file__).parent.parent.parent / config_path
    with open(config_file, "r", encoding="utf-8") as f:
        yaml_config = yaml.safe_load(f)

    # Substitute environment variables in YAML
    yaml_config = _substitute_env_vars(yaml_config)

    # Create Config object (will also load from .env)
    config = Config(**yaml_config)

    # Override with environment variables if present
    if config.aliyun_api_key:
        config.ai.api_key = config.aliyun_api_key
    if config.admin_email:
        config.monitoring.admin_email = config.admin_email

    return config


def _substitute_env_vars(config: Any) -> Any:
    """
    Recursively substitute ${VAR_NAME} with environment variables.

    Args:
        config: Configuration dict or value

    Returns:
        Configuration with substituted values
    """
    if isinstance(config, dict):
        return {k: _substitute_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [_substitute_env_vars(item) for item in config]
    elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
        var_name = config[2:-1]
        return os.getenv(var_name, "")
    else:
        return config


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get global config instance (singleton)."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
