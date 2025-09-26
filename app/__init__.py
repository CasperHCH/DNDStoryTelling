from fastapi import FastAPI
from app.routes import auth, story, confluence
from app.models.database import init_db

app = FastAPI(title="D&D Story Telling")

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/")
async def root():
    return {"message": "D&D Story Telling API"}

app.include_router(auth.router)
app.include_router(story.router)
app.include_router(confluence.router)