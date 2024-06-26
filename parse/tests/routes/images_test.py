from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from beanie import PydanticObjectId
from config import Settings
from database import Database
from fastapi import FastAPI, UploadFile, status
from models import Image, Project
from routes.images import router
from service.images import ImagesWorker

app = FastAPI()
app.include_router(router)
config = Settings()
worker = ImagesWorker(config.BUCKET_NAME)
db = Database(Image)


async def init_db():
    test_settings = Settings()
    test_settings.DATABASE_URL = "mongodb://localhost:27017/testdb"
    test_settings.BUCKET_NAME = "bucket3test"
    await test_settings.initialize_database()


def create_s3_session():
    return MagicMock()


@pytest.fixture
async def client():
    await init_db()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://app"
    ) as client:
        yield client
    await Image.find_all().delete()
    await Project.find_all().delete()


@pytest.fixture
def project_id() -> PydanticObjectId:
    return PydanticObjectId()


@pytest.fixture
def image_file() -> UploadFile:
    file_mock = MagicMock(spec=UploadFile)
    file_mock.content_type = "image/png"
    file_mock.filename = "test.png"
    file_mock.read = AsyncMock(return_value=b"file bytes")
    return file_mock


@pytest.mark.asyncio
async def test_upload_image_success(client):
    project = Project(name="test")
    project_doc = await Project.create(project)
    headers = {"accept": "application/json"}
    files = {"image": ("test.png", b"file bytes", "image/png")}
    params = {"project_id": str(project_doc.id)}

    response = await client.post("/", headers=headers, params=params, files=files)
    assert response.status_code == status.HTTP_201_CREATED
    assert "image" in response.json()


@pytest.mark.asyncio
async def test_upload_image_invalid_content_type(client):
    project = Project(name="test")
    project_doc = await Project.create(project)
    headers = {"accept": "application/json"}
    files = {"image": ("test.txt", b"file bytes", "text/plain")}
    params = {"project_id": str(project_doc.id)}

    response = await client.post("/", headers=headers, params=params, files=files)
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
    assert response.json()["detail"] == "This is not image."


@pytest.mark.asyncio
async def test_download_image_not_found(client):
    with patch.object(db, "get", return_value=None):
        response = await client.get(f"/{PydanticObjectId()}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Not found."


@pytest.mark.asyncio
async def test_get_images_info(client):
    image = Image(filename="test", path="test/test.png", project_id=PydanticObjectId())
    await Image.save(image)
    response = await client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_delete_images_info(client):
    images = [
        Image(
            project_id=PydanticObjectId(),
            path="path/to/image",
            filename="test.png",
        )
    ]
    with patch.object(db, "get_all", return_value=images):
        with patch.object(db, "delete"):
            response = await client.delete("/")

            assert response.status_code == status.HTTP_200_OK
            assert response.json()["message"] == "successfully."
