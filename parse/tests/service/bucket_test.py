from io import BytesIO
from unittest.mock import AsyncMock, patch

import pytest
from responses.s3_response import S3Stream
from service.buckets import BucketWorker


class BucketWorkerTest(BucketWorker):
    pass


class TestBucketWorker:
    @pytest.fixture
    def bucket_worker(self) -> BucketWorkerTest:
        return BucketWorkerTest(bucket="buckets3test")

    def test_create_temp_file(self, bucket_worker: BucketWorkerTest):
        test_bytes = b"test data"
        temp_file = bucket_worker.create_temp_file(test_bytes)

        assert isinstance(temp_file, BytesIO)
        assert temp_file.read() == test_bytes

    @pytest.mark.asyncio
    async def test_upload_file_success(self, bucket_worker: BucketWorkerTest):
        s3_mock = AsyncMock()
        s3_mock.upload_fileobj = AsyncMock()
        temp_file = BytesIO(b"test data")
        blob_s3_key = "test/key"

        result = await bucket_worker.upload_file(s3_mock, blob_s3_key, temp_file)

        s3_mock.upload_fileobj.assert_called_once_with(
            temp_file, bucket_worker.bucket, blob_s3_key
        )
        assert result == blob_s3_key

    @pytest.mark.asyncio
    async def test_upload_file_failure(self, bucket_worker: BucketWorkerTest):
        s3_mock = AsyncMock()
        s3_mock.upload_fileobj = AsyncMock(side_effect=Exception("Upload failed"))
        temp_file = BytesIO(b"test data")
        blob_s3_key = "test/key"

        with patch("logging.error") as mock_logging_error:
            result = await bucket_worker.upload_file(s3_mock, blob_s3_key, temp_file)
            mock_logging_error.assert_called_once()

        s3_mock.upload_fileobj.assert_called_once_with(
            temp_file, bucket_worker.bucket, blob_s3_key
        )
        assert result == ""

    @pytest.mark.asyncio
    async def test_download_file_stream(self, bucket_worker: BucketWorkerTest):
        blob_s3_key = "test/key"
        result = await bucket_worker.download_file_stream(blob_s3_key)

        assert isinstance(result, S3Stream)
        assert result.Bucket == bucket_worker.bucket
        assert result.Key == blob_s3_key
