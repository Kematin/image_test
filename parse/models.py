from beanie import Document, PydanticObjectId
from pydantic import BaseModel


class Project(Document):
    name: str

    class Settings:
        name = "projects"

    class Config:
        json_schema_extra = {"example": {"name": "Project"}}


class ProjectUpdate(BaseModel):
    name: str

    class Config:
        json_schema_extra = {"example": {"name": "Project"}}


class Image(Document):
    project_id: PydanticObjectId
    path: str
    filename: str

    class Settings:
        name = "images"


class ImageSocketMessage(BaseModel):
    image_id: PydanticObjectId | str
    state: str
    project_id: PydanticObjectId
