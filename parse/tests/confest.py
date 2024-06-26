import asyncio

import httpx
import pytest
from config import Settings
from main import app
from models import Image, Project


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


async def init_db():
    test_settings = Settings()
    test_settings.DATABASE_URL = "mongodb://localhost:27017/testdb"
    test_settings.BUCKET_NAME = "bucket3test"
    await test_settings.initialize_database()


@pytest.fixture(scope="session")
async def default_client():
    await init_db()
    async with httpx.AsyncClient(app=app, base_url="http://app") as client:
        yield client
        # Clean db
        await Image.find_all().delete()
        await Project.find_all().delete()
