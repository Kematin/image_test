from aioboto3 import Session
from beanie import PydanticObjectId
from exceptions import UniqueException
from fastapi import UploadFile
from models import Image, ImageSocketMessage
from responses.s3_response import S3Stream

from service.buckets import BucketWorker
from service.socket import WebSocketManager


class ImagesWorker(BucketWorker):
    def __init__(self, bucket: str):
        super().__init__(bucket)

    async def __check_unique_path(self, path: str) -> bool:
        image = await Image.find_one(Image.path == path)
        if image:
            return False
        return True

    async def send_socket_message(
        self,
        project_id: PydanticObjectId,
        image_id: PydanticObjectId = "soon",
        state: str = "init",
    ):
        socket_manager = WebSocketManager()
        message = ImageSocketMessage(
            project_id=project_id, image_id=image_id, state=state
        )
        await socket_manager.send_message(project_id, message)

    async def upload_image(
        self,
        s3: Session,
        file: UploadFile,
        project_id: PydanticObjectId,
        object_name: str = None,
    ) -> str:
        # If S3 object_name was not specified, use file_name
        await self.send_socket_message(project_id)
        if object_name is None:
            object_name = file.filename

        blob_s3_key = f"images/{project_id}/{object_name}"

        if not await self.__check_unique_path(blob_s3_key):
            await self.send_socket_message(project_id, image_id="no", state="error")
            raise UniqueException

        bytes = await file.read()
        temp_file = self.create_temp_file(bytes)
        await self.send_socket_message(project_id, image_id="soon", state="processing")
        return await self.upload_file(s3, blob_s3_key, temp_file)

    async def download_image_response(self, image: Image) -> S3Stream:
        blob_s3_key = image.path
        return await self.download_file_stream(blob_s3_key)
