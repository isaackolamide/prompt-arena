import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.auth import router as auth_router

logger = logging.getLogger("app")

app = FastAPI(
    title="Prompt Arena API",
    description="Backend API for Prompt Arena",
    version="0.1.0",
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the auth router
app.include_router(auth_router)

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint hit")
    return {"status": "ok", "environment": settings.ENV}
