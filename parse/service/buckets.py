import logging
from abc import ABC
from io import BytesIO

from aioboto3 import Session
from responses.s3_response import S3Stream


class BucketWorker(ABC):
    def __init__(self, bucket: str):
        self.bucket = bucket

    def create_temp_file(self, bytes: bytes) -> BytesIO:
        temp_file = BytesIO()
        temp_file.write(bytes)
        temp_file.seek(0)
        return temp_file

    async def upload_file(
        self, s3: Session, blob_s3_key: str, temp_file: BytesIO
    ) -> str:
        try:
            await s3.upload_fileobj(temp_file, self.bucket, blob_s3_key)
            logging.info(f"Finished Uploading {blob_s3_key} to s3")
        except Exception as e:
            logging.error(f"Unable to s3 upload to {blob_s3_key}: {e} ({type(e)})")
            return ""

        return blob_s3_key

    async def download_file_stream(self, blob_s3_key: str) -> S3Stream:
        return S3Stream(content=None, Bucket=self.bucket, Key=blob_s3_key)
