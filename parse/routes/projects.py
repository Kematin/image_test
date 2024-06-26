import logging

from beanie import PydanticObjectId
from database import Database
from fastapi import (
    APIRouter,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import JSONResponse
from models import Project, ProjectUpdate
from service.socket import WebSocketManager

router = APIRouter()
db = Database(Project)


@router.get("/")
async def retieve_all():
    projects = await db.get_all()
    return projects


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create(data: Project):
    created_project = await db.create(data)
    return JSONResponse({"project": created_project.model_dump()})


@router.delete("/")
async def delete_all_projects():
    all_projects = await db.get_all()
    for project in all_projects:
        await db.delete(project.id)
    return JSONResponse({"message": "successfully."})


@router.get("/{id}")
async def retieve_single(id: PydanticObjectId):
    project = await db.get(id)
    if not project:
        raise HTTPException(detail="Not found.", status_code=status.HTTP_404_NOT_FOUND)
    return JSONResponse({"project": project.model_dump()})


@router.delete("/{id}")
async def delete_single_project(id: PydanticObjectId):
    project = await db.delete(id)
    if not project:
        raise HTTPException(detail="Not found.", status_code=status.HTTP_404_NOT_FOUND)
    return JSONResponse({"message": "successfully."})


@router.put("/{id}")
async def update(id: PydanticObjectId, data: ProjectUpdate):
    updated_project = await db.update(id, data)
    if not updated_project:
        raise HTTPException(detail="Not found.", status_code=status.HTTP_404_NOT_FOUND)
    return JSONResponse({"project": updated_project})


@router.websocket("/{id}/images")
async def retieve_images_status(*, websocket: WebSocket, id: PydanticObjectId):
    project = await db.get(id)
    if not project:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Project not found."
        )

    websocket_manager = WebSocketManager()
    await websocket_manager.connect(id, websocket)
    try:
        while True:
            await websocket_manager.send_images_uploaded(websocket, id)
            await websocket.receive_text()
    except WebSocketDisconnect:
        await websocket_manager.disconnect(id, websocket)
        logging.info("client disconnected")
