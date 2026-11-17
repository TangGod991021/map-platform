from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError

from app.api.admin import router as admin_router
from app.api.map_public import router as public_router
from app.config import ensure_dirs, settings
from app.database import SessionLocal
from app.seed import seed_data

ensure_dirs()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 表结构由 Alembic 管理；首次启动前执行：alembic upgrade head
    try:
        async with SessionLocal() as db:
            await seed_data(db)
    except OperationalError as exc:
        raise RuntimeError("数据库表不存在，请先执行 `alembic upgrade head`") from exc
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router, prefix=settings.api_prefix)
app.include_router(public_router, prefix=settings.public_prefix)
app.mount("/profile", StaticFiles(directory=settings.upload_dir), name="profile")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "msg": str(exc.detail), "success": False},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"code": 422, "msg": "参数校验失败", "success": False, "detail": exc.errors()},
    )


@app.get("/", summary="健康检查")
async def health():
    return {"name": settings.app_name, "status": "ok", "env": settings.app_env}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
