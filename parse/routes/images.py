from aioboto3 import Session
from beanie import PydanticObjectId
from config import config
from database import Database
from exceptions import UniqueException
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from models import Image, Project
from service.images import ImagesWorker

router = APIRouter()
db = Database(Image)
worker = ImagesWorker(config.BUCKET_NAME)


async def create_s3_session():
    session = Session()
    async with session.client("s3") as s3:
        yield s3


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_image(
    project_id: PydanticObjectId,
    image: UploadFile = File(...),
    s3=Depends(create_s3_session),
):
    if "image" not in image.content_type:
        raise HTTPException(
            detail="This is not image.", status_code=status.HTTP_406_NOT_ACCEPTABLE
        )
    if not await Database(Project).get(project_id):
        raise HTTPException(
            detail="Project not found.", status_code=status.HTTP_404_NOT_FOUND
        )
    try:
        path = await worker.upload_image(s3, image, project_id)
    except UniqueException:
        raise HTTPException(
            detail="Image already in storage.", status_code=status.HTTP_409_CONFLICT
        )
    if not path:
        raise HTTPException(
            detail="Image wasnt uploaded.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    image_doc = await db.create(
        Image(project_id=project_id, path=path, filename=image.filename)
    )
    await worker.send_socket_message(project_id, image_id=image_doc.id, state="done")
    downloand_link = f"{config.HOST_URL}/images/{image_doc.id}"
    image_response = image_doc.model_dump()
    image_response["download_link"] = downloand_link
    return JSONResponse({"image": image_response})


@router.get("/{id}")
async def download_image(id: PydanticObjectId):
    image_document = await db.get(id)
    if not image_document:
        raise HTTPException(detail="Not found.", status_code=status.HTTP_404_NOT_FOUND)
    response = await worker.download_image_response(image_document)
    if not response:
        raise HTTPException(
            detail="Image wasnt downloaded.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return response


@router.get("/")
async def get_images_info():
    images = await db.get_all()
    return images


@router.delete("/")
async def delete_images_info():
    images = await db.get_all()
    for image in images:
        await db.delete(image.id)
    return JSONResponse({"message": "successfully."})
