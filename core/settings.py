from pydantic_settings import BaseSettings
from typing import Optional, Dict
import os


class Settings(BaseSettings):
    app_name: str = "Marin"
    debug: bool = True
    
    # Multi-Model LLM Support
    # Primary: Groq (free tier available)
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"
    
    # Secondary: Mistral
    mistral_api_key: Optional[str] = None
    mistral_model: str = "mistral-large-latest"
    
    # Vision model for Screen Reading
    vision_model: str = "llama-3.2-90b-vision-preview"
    
    # Embeddings model for semantic memory
    embeddings_model: str = "text-embedding-3-small"
    
    # Default provider: groq (free) or mistral
    llm_provider: str = "groq"
    
    # Model Settings
    temperature: float = 0.8
    max_tokens: int = 120
    
    # Memory Settings
    memory_db_path: str = "./data/marin.db"
    vector_db_path: str = "./data/vector_db"
    reflection_summary_length: int = 200
    max_context_messages: int = 20
    
    # Agent Settings
    agent_timeout: int = 30
    max_tool_calls: int = 5
    
    # Voice Settings
    tts_engine: str = "edge"
    stt_engine: str = "whisper"
    
    # Proactive Settings
    inactivity_threshold_minutes: int = 30
    proactive_enabled: bool = True
    
    # Emotional Engine
    default_mood: str = "happy"
    mood_intensity: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_chat_model(self) -> str:
        if self.llm_provider == "mistral":
            return self.mistral_model
        return self.groq_model
    
    def get_embeddings_model(self) -> str:
        return self.embeddings_model
    
    def get_model_for_task(self, task: str) -> str:
        models: Dict[str, str] = {
            "chat": self.get_chat_model(),
            "embeddings": self.embeddings_model,
            "fast": self.groq_model,
            "vision": self.vision_model
        }
        return models.get(task, self.get_chat_model())


settings = Settings()

os.makedirs("./data", exist_ok=True)
os.makedirs(settings.vector_db_path, exist_ok=True)