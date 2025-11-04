try:
    from pydantic_settings import BaseSettings  # type: ignore[import-not-found]
except Exception:
    # Fallback minimal shim if pydantic-settings n'est pas installé
    class BaseSettings:  # type: ignore
        pass
from typing import List
import os


class Settings(BaseSettings):
    # API
    ALLOW_ORIGINS: List[str] = ["*"]

    # Model directory
    MODEL_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

    # Qdrant
    QDRANT_HOST: str = os.environ.get("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.environ.get("QDRANT_PORT", 6333))


settings = Settings()


