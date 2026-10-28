import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.config import settings
from app.database.session import init_db
from app.services.seed_data import seed_database_if_empty
from app.api.endpoints import router as api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database tables and seeds
    logger.info("Initializing database...")
    init_db()
    logger.info("Seeding realistic sample inspections if database is empty...")
    seed_database_if_empty()
    logger.info("Manufacturing Defect Detection System backend ready.")
    yield
    # Shutdown
    logger.info("Shutting down backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Full-stack AI-Based Industrial Defect Detection System with PyTorch, OpenCV, and FastAPI.",
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
is_wildcard_cors = "*" in settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=not is_wildcard_cors,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error processing {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error occurred. Please check server logs."}
    )

# Static file serving for inspection images
app.mount("/api/images/original", StaticFiles(directory=str(settings.ORIGINAL_UPLOAD_DIR)), name="original_images")
app.mount("/api/images/annotated", StaticFiles(directory=str(settings.ANNOTATED_UPLOAD_DIR)), name="annotated_images")

# Register API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "message": "AI-Based Manufacturing Defect Detection System API",
        "documentation": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
