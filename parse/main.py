from contextlib import asynccontextmanager

import uvicorn
from config import config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.api import api_router


# lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    await config.initialize_database()
    yield


# app
app = FastAPI(
    lifespan=lifespan,
    title="Upload Image",
    description="Simple Image Upload To S3 With Websockets",
)


# routes
app.include_router(api_router)


# middleware
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=config.PORT, reload=True)
