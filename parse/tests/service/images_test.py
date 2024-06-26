from unittest.mock import AsyncMock, patch

import pytest
from beanie import PydanticObjectId
from exceptions import UniqueException
from fastapi import UploadFile
from models import Image
from responses.s3_response import S3Stream
from service.images import ImagesWorker


class TestImagesWorker:
    @pytest.fixture
    def images_worker(self) -> ImagesWorker:
        return ImagesWorker(bucket="buckets3test")

    @pytest.mark.asyncio
    async def test_check_unique_path(self, images_worker: ImagesWorker):
        with patch.object(Image, "find_one", return_value=None):
            result = await images_worker._ImagesWorker__check_unique_path("unique/path")
            assert result is True

        with patch.object(Image, "find_one", return_value=Image(path="unique/path")):
            result = await images_worker._ImagesWorker__check_unique_path("unique/path")
            assert result is False

    @pytest.mark.asyncio
    async def test_send_socket_message(self, images_worker: ImagesWorker):
        with patch(
            "service.socket.WebSocketManager.send_message", new_callable=AsyncMock
        ) as mock_send_message:
            project_id = PydanticObjectId()
            image_id = "soon"
            state = "state"
            await images_worker.send_socket_message(project_id, image_id, state)
            mock_send_message.assert_called_once()
            args, kwargs = mock_send_message.call_args
            assert args[0] == project_id
            assert args[1].project_id == project_id
            assert args[1].image_id == image_id
            assert args[1].state == state

    @pytest.mark.asyncio
    async def test_upload_image_success(self, images_worker: ImagesWorker):
        with patch.object(Image, "find_one", return_value=None):
            s3_mock = AsyncMock()
            upload_file_mock = AsyncMock(spec=UploadFile)
            upload_file_mock.filename = "test.png"
            upload_file_mock.read = AsyncMock(return_value=b"file bytes")

            project_id = PydanticObjectId()
            result = await images_worker.upload_image(
                s3_mock, upload_file_mock, project_id
            )

            assert result == f"images/{project_id}/test.png"

    @pytest.mark.asyncio
    async def test_upload_image_non_unique_path(self, images_worker: ImagesWorker):
        with patch.object(
            Image, "find_one", return_value=Image(path="images/project_id/test.png")
        ):
            with pytest.raises(UniqueException):
                s3_mock = AsyncMock()
                upload_file_mock = AsyncMock(spec=UploadFile)
                upload_file_mock.filename = "test.png"
                upload_file_mock.read = AsyncMock(return_value=b"file bytes")

                project_id = PydanticObjectId()
                await images_worker.upload_image(s3_mock, upload_file_mock, project_id)

    @pytest.mark.asyncio
    async def test_download_image_response(self, images_worker: ImagesWorker):
        project_id = PydanticObjectId()
        image = Image(
            project_id=project_id,
            filename="test.png",
            path=f"images/{project_id}/test.png",
        )
        result = await images_worker.download_image_response(image)

        assert isinstance(result, S3Stream)
        assert result.Bucket == images_worker.bucket
        assert result.Key == "images/project_id/test.png"
