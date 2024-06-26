from unittest.mock import AsyncMock

import pytest
from beanie import PydanticObjectId
from config import Settings
from fastapi import WebSocket
from models import Image, ImageSocketMessage
from service.socket import WebSocketManager


async def init_db():
    test_settings = Settings()
    test_settings.DATABASE_URL = "mongodb://localhost:27017/testdb"
    test_settings.BUCKET_NAME = "bucket3test"
    await test_settings.initialize_database()


class TestWebSocketManager:
    @pytest.fixture()
    async def client(self):
        await init_db()
        yield
        await Image.find_all().delete()

    @pytest.fixture
    def websocket_manager(self) -> WebSocketManager:
        return WebSocketManager()

    @pytest.fixture
    def project_id(self) -> PydanticObjectId:
        return PydanticObjectId()

    @pytest.fixture
    def websocket(self) -> WebSocket:
        websocket_mock = AsyncMock(spec=WebSocket)
        websocket_mock.accept = AsyncMock()
        websocket_mock.send_json = AsyncMock()
        return websocket_mock

    def test_singleton_behavior(self):
        instance1 = WebSocketManager()
        instance2 = WebSocketManager()
        assert instance1 is instance2

    @pytest.mark.asyncio
    async def test_connect(
        self,
        websocket_manager: WebSocketManager,
        project_id: PydanticObjectId,
        websocket: WebSocket,
    ):
        await websocket_manager.connect(project_id, websocket)
        assert project_id in websocket_manager.active_connections
        assert websocket in websocket_manager.active_connections[project_id]
        websocket.accept.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_disconnect(
        self,
        websocket_manager: WebSocketManager,
        project_id: PydanticObjectId,
        websocket: WebSocket,
    ):
        with pytest.raises(KeyError):
            await websocket_manager.connect(project_id, websocket)
            await websocket_manager.disconnect(project_id, websocket)
            websocket in websocket_manager.active_connections[project_id]

    @pytest.mark.asyncio
    async def test_send_images_uploaded(
        self,
        client,
        websocket_manager: WebSocketManager,
        project_id: PydanticObjectId,
        websocket: WebSocket,
    ):
        image = Image(filename="test.png", path="test/test.png", project_id=project_id)
        await image.create()
        await websocket_manager.send_images_uploaded(websocket, project_id)
        websocket.send_json.assert_awaited_once()
        args, kwargs = websocket.send_json.call_args
        assert "images" in args[0]

    @pytest.mark.asyncio
    async def test_send_message(
        self,
        websocket_manager: WebSocketManager,
        project_id: PydanticObjectId,
        websocket: WebSocket,
    ):
        await websocket_manager.connect(project_id, websocket)
        message = ImageSocketMessage(
            image_id=PydanticObjectId(), state="uploaded", project_id=project_id
        )
        await websocket_manager.send_message(project_id, message)
        websocket.send_json.assert_awaited_once_with(message.model_dump())
