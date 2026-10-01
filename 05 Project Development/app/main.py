import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import router

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Ensure required static directories exist
os.makedirs(os.path.join(STATIC_DIR, "panels"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "exports"), exist_ok=True)

app = FastAPI(
    title="ComicCraft - AI Comic Story Creator",
    description="Generate personalized 5-panel comic book stories and illustrations using Google Gemini and Stable Diffusion.",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include application routes
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
