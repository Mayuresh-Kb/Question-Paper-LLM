import asyncio
import logging
from contextlib import asynccontextmanager, suppress
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from app.api.endpoints import router
from app.core import config
from app.core.utils import cleanup_expired


class CachedStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers.setdefault("Cache-Control", "public, max-age=31536000, immutable")
        return response

@asynccontextmanager
async def lifespan(app):
    config.create_storage_directories()
    await run_in_threadpool(cleanup_expired)
    async def clean_periodically():
        while True:
            await asyncio.sleep(3600)
            await run_in_threadpool(cleanup_expired)
    cleaner = asyncio.create_task(clean_periodically())
    yield
    cleaner.cancel()
    with suppress(asyncio.CancelledError):
        await cleaner

def create_app(frontend_dist=None):
    application = FastAPI(title="Question Paper Generator", version="1.0.0", lifespan=lifespan)
    application.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "X-Session-Token"])
    # Root routes preserve the local API and existing integrations. The /api
    # alias lets the built frontend and backend share one production origin.
    application.include_router(router)
    application.include_router(router, prefix="/api", include_in_schema=False)

    static_root = frontend_dist if frontend_dist is not None else config.FRONTEND_DIST
    if static_root:
        static_root = static_root.resolve()
        index = static_root / "index.html"
        if not index.is_file():
            raise RuntimeError(f"FRONTEND_DIST does not contain index.html: {static_root}")
        assets = static_root / "assets"
        if assets.is_dir():
            application.mount("/assets", CachedStaticFiles(directory=assets), name="frontend-assets")

        @application.get("/{full_path:path}", include_in_schema=False)
        def frontend(full_path: str):
            # Never turn an unknown API URL into a misleading HTML success.
            if full_path == "api" or full_path.startswith("api/"):
                raise HTTPException(404, "API route not found.")
            candidate = (static_root / full_path).resolve()
            try:
                candidate.relative_to(static_root)
            except ValueError:
                raise HTTPException(404, "File not found.")
            if candidate.is_file():
                return FileResponse(candidate, headers={"Cache-Control": "public, max-age=3600"})
            return FileResponse(index, headers={"Cache-Control": "no-cache"})
    return application


logging.basicConfig(level=logging.INFO)
app = create_app()
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
