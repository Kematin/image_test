from fastapi import APIRouter

from routes import images, projects

api_router = APIRouter()
api_router.include_router(images.router, prefix="/images", tags=["Work with images"])
api_router.include_router(
    projects.router, prefix="/projects", tags=["Work with projects"]
)
