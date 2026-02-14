#!/usr/bin/env python3
"""快速测试 Newsloom API Server 功能"""

import asyncio
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_server():
    """测试服务器组件"""
    print("=" * 60)
    print("🧪 NEWSLOOM API SERVER - COMPONENT TEST")
    print("=" * 60)
    print()

    # Test 1: Import main app
    print("1️⃣  Testing FastAPI app import...")
    try:
        from server.main import app
        print(f"   ✓ App imported: {app.title} v{app.version}")
        print(f"   ✓ Routes registered: {len(app.routes)}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Test 2: Database models
    print("\n2️⃣  Testing database models...")
    try:
        from server.database import (
            Report,
            Article,
            PipelineRun,
            SourceConfig,
            Setting,
        )
        print("   ✓ All models imported successfully")
        print(f"   ✓ Tables: Report, Article, PipelineRun, SourceConfig, Setting")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Test 3: Database initialization
    print("\n3️⃣  Testing database initialization...")
    try:
        from server.database import init_db, engine

        await init_db()
        print("   ✓ Database initialized")
        print(f"   ✓ Engine: {engine.url}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Test 4: Schemas
    print("\n4️⃣  Testing Pydantic schemas...")
    try:
        from server.schemas import (
            ReportResponse,
            ArticleResponse,
            PipelineRunRequest,
            SourceConfigResponse,
            WSMessage,
        )
        print("   ✓ All schemas imported successfully")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Test 5: Services
    print("\n5️⃣  Testing services...")
    try:
        from server.services.pipeline_service import pipeline_service
        from server.services.report_service import report_service

        print("   ✓ pipeline_service loaded")
        print("   ✓ report_service loaded")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Test 6: Routers
    print("\n6️⃣  Testing routers...")
    try:
        from server.routers import reports, sources, pipeline, ws

        print(f"   ✓ reports router: {len(reports.router.routes)} routes")
        print(f"   ✓ sources router: {len(sources.router.routes)} routes")
        print(f"   ✓ pipeline router: {len(pipeline.router.routes)} routes")
        print(f"   ✓ ws router: {len(ws.router.routes)} routes")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Test 7: Config
    print("\n7️⃣  Testing configuration...")
    try:
        from server.config import settings

        print(f"   ✓ App name: {settings.app_name}")
        print(f"   ✓ Host: {settings.host}:{settings.port}")
        print(f"   ✓ Database: {settings.db_url}")
        print(f"   ✓ CORS origins: {', '.join(settings.cors_origins)}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Test 8: List all API endpoints
    print("\n8️⃣  API Endpoints:")
    from server.main import app

    api_routes = [
        route
        for route in app.routes
        if hasattr(route, "path") and route.path.startswith("/api")
    ]

    for route in sorted(api_routes, key=lambda r: r.path):
        if hasattr(route, "methods"):
            methods = ", ".join(sorted(route.methods - {"HEAD", "OPTIONS"}))
            print(f"   {methods:8} {route.path}")

    # Test 9: WebSocket endpoint
    print("\n9️⃣  WebSocket:")
    ws_routes = [route for route in app.routes if hasattr(route, "path") and route.path == "/ws"]
    if ws_routes:
        print("   ✓ ws://localhost:8080/ws")

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print()
    print("🚀 Ready to start server:")
    print("   python -m server.main")
    print()
    print("📚 Documentation:")
    print("   http://localhost:8080/docs")
    print()

    return True


if __name__ == "__main__":
    success = asyncio.run(test_server())
    sys.exit(0 if success else 1)
