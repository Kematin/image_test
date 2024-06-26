from typing import Dict, List

from beanie import PydanticObjectId
from fastapi import WebSocket
from models import Image, ImageSocketMessage


class WebSocketManager:
    _instance = None
    active_connections: Dict[str, List[WebSocket]] = {}

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    async def connect(self, project_id: PydanticObjectId, websocket: WebSocket):
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)
        await websocket.accept()

    async def disconnect(self, project_id: PydanticObjectId, websocket: WebSocket):
        self.active_connections[project_id].remove(websocket)
        if not self.active_connections[project_id]:
            del self.active_connections[project_id]

    async def __get_documents(
        self, project_id: PydanticObjectId
    ) -> List[ImageSocketMessage]:
        images = await Image.find(Image.project_id == project_id).to_list()
        answers_list = list()
        for image in images:
            answer = ImageSocketMessage(
                image_id=image.id, state="uploaded", project_id=project_id
            )
            answers_list.append(answer)
        return answers_list

    async def send_images_uploaded(
        self, websocket: WebSocket, project_id: PydanticObjectId
    ):
        answers = await self.__get_documents(project_id)
        answers_json = [answer.model_dump() for answer in answers]
        await websocket.send_json({"images": answers_json})

    async def send_message(
        self, project_id: PydanticObjectId, message: ImageSocketMessage
    ):
        print(self.active_connections)
        if project_id in self.active_connections:
            for connection in self.active_connections[project_id]:
                print(connection)
                await connection.send_json(message.model_dump())
