from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.models.database import init_db
from app.routes import auth, confluence, story


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="D&D Story Telling", lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "D&D Story Telling API"}


app.include_router(auth.router)
app.include_router(story.router)
app.include_router(confluence.router)
