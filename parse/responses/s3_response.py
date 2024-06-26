import typing

from aioboto3 import Session
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask


class S3Stream(StreamingResponse):
    def __init__(
        self,
        content: typing.Any,
        status_code: int = 200,
        headers: dict = None,
        media_type: str = None,
        background: BackgroundTask = None,
        Key: str = None,
        Bucket: str = None,
    ) -> None:
        super(S3Stream, self).__init__(
            content, status_code, headers, media_type, background
        )
        self.Key = Key
        self.Bucket = Bucket

    async def stream_response(self, send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.raw_headers,
            }
        )

        session = Session()
        async with session.client("s3") as client:
            result = await client.get_object(Bucket=self.Bucket, Key=self.Key)

            async for chunk in result["Body"]:
                if not isinstance(chunk, bytes):
                    chunk = chunk.encode(self.charset)

                await send(
                    {"type": "http.response.body", "body": chunk, "more_body": True}
                )

        await send({"type": "http.response.body", "body": b"", "more_body": False})
