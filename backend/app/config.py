from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union
import json

class Settings(BaseSettings):
    """
    Configuration settings for the application.
    WHY: Using BaseSettings allows us to read from environment variables or .env file automatically.
    It also provides type validation out of the box.
    """
    GEMINI_API_KEY: str = ""  # WHY: Default to empty so app starts without .env; fails gracefully at AI call time
    GROQ_API_KEY: str = ""    # WHY: Groq API Key for ultra-fast 200ms Llama 3.3 70B inference
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"  # WHY: Local Ollama endpoint for fine-tuned Llama 3
    GITHUB_TOKEN: str = ""     # Optional GitHub PAT to bypass 60 req/hr rate limits (boosts to 5000 req/hr)
    AWS_REGION: str = "ap-south-1"
    S3_BUCKET_NAME: str = "resume-grind-uploads"
    DYNAMODB_TABLE_NAME: str = "resume-grind-sessions"
    ENVIRONMENT: str = "dev"
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"]


    # Model Config
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def get_cors_origins(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, str):
            try:
                # In case it's a JSON string
                parsed = json.loads(self.CORS_ORIGINS)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                # Otherwise split by comma
                return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]
        return self.CORS_ORIGINS

settings = Settings()
