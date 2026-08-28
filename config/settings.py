from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    PROJECT_NAME: str = "Engineering Pattern Evaluation & Decision Engine"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    
    # Storage settings
    DATA_DIR: Path = BASE_DIR / "data"
    CHROMA_PERSIST_DIR: Path = DATA_DIR / "chroma"
    GRAPH_PERSIST_FILE: Path = DATA_DIR / "evidence_graph.json"
    SEEDS_DIR: Path = BASE_DIR / "seeds"
    
    # Sandbox settings
    SANDBOX_TIMEOUT_SECONDS: int = 30
    SANDBOX_WORK_DIR: Path = DATA_DIR / "sandbox"
    
    # LLM Settings
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o"
    
    # Evidence scoring parameters
    CONFIDENCE_HALF_LIFE_DAYS: float = 180.0  # 6 months half life for freshness

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
settings.SANDBOX_WORK_DIR.mkdir(parents=True, exist_ok=True)
