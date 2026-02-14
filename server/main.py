"""FastAPI main application"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from server.config import settings
from server.database import init_db
from server.routers import reports, sources, pipeline, ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events"""
    # Startup
    print("🚀 Initializing Newsloom API Server...")
    print(f"   - Database: {settings.db_url}")
    print(f"   - Reports dir: {settings.reports_dir}")

    # Initialize database
    await init_db()
    print("   ✓ Database initialized")

    yield

    # Shutdown
    print("👋 Shutting down Newsloom API Server...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Newsloom Intelligence Pipeline API",
    lifespan=lifespan,
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(reports.router)
app.include_router(sources.router)
app.include_router(pipeline.router)
app.include_router(ws.router)


# Root endpoint
@app.get("/")
async def root():
    """API root"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "detail": str(exc.detail) if hasattr(exc, "detail") else "Resource not found"},
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🗞️  NEWSLOOM API SERVER                                ║
║                                                           ║
║   Running at: http://{settings.host}:{settings.port}                      ║
║   Docs: http://{settings.host}:{settings.port}/docs                      ║
║   WebSocket: ws://{settings.host}:{settings.port}/ws                     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "server.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
    )
