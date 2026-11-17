from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = API_ROOT.parents[1]


class Settings(BaseSettings):
    app_name: str = "Qianshan Manyou API"
    app_env: str = "dev"
    api_prefix: str = "/prod-api"
    public_prefix: str = "/map-api/v1"

    database_url: str = (
        f"sqlite+aiosqlite:///{(API_ROOT / 'data' / 'map_platform.db').as_posix()}"
    )
    jwt_secret: str = "CHANGE_ME_TO_A_LONG_RANDOM_SECRET"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720

    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "https://tianmap.mengyu.live,https://map-admin.mengyu.live"
    )
    upload_dir: str = str(API_ROOT / "data" / "uploads")
    map_publish_dir: str = str(PROJECT_ROOT / "apps" / "map-web" / "data")
    # 贵州省界 GeoJSON；生产环境可指向独立部署的边界文件
    geo_boundary_path: str = str(PROJECT_ROOT / "apps" / "map-web" / "data" / "guizhou.json")
    tianditu_tk: str = ""

    model_config = SettingsConfigDict(
        env_file=API_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()


def ensure_dirs() -> None:
    for directory in (
        API_ROOT / "data",
        Path(settings.upload_dir),
        Path(settings.map_publish_dir),
    ):
        directory.mkdir(parents=True, exist_ok=True)
