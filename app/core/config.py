from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL","http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL","phi3")
    top_k: int = int(os.getenv("TOP_K", "6"))
    llm_timeout: int = int(os.getenv("LLM_TIMEOUT", "30"))

    data_dir: str = os.getenv("DATA_DIR", "data")
    index_dir: str = os.getenv("INDEX_DIR", "index")
    sqlite_path: str = os.getenv("SQLITE_PATH", "index/patients.sqlite3")

settings = Settings()
