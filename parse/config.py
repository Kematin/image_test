from pathlib import Path

from beanie import init_beanie
from models import Image, Project
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PORT: int = 8000
    DATABASE_URL: str
    BUCKET_NAME: str
    HOST_URL: str = f"http://127.0.0.1:{PORT}"

    async def initialize_database(self):
        client = AsyncIOMotorClient(self.DATABASE_URL)
        await init_beanie(
            database=client.get_default_database(), document_models=[Project, Image]
        )

    class Config:
        __base_dir = Path(__file__).resolve().parent
        env_file = f"{__base_dir}/.env"


config = Settings()
