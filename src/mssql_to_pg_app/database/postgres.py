import ssl
import asyncpg
from etl_app.config import required_env
from etl_app.models import AppSettings

async def create_pool(settings: AppSettings) -> asyncpg.Pool:
    sslmode = required_env("POSTGRES_SSLMODE").lower()
    ssl_context = None
    if sslmode not in {"disable", "allow", "prefer"}:
        ssl_context = ssl.create_default_context()
    return await asyncpg.create_pool(
        host=required_env("POSTGRES_HOST"),
        port=int(required_env("POSTGRES_PORT")),
        database=required_env("POSTGRES_DATABASE"),
        user=required_env("POSTGRES_USER"),
        password=required_env("POSTGRES_PASSWORD"),
        min_size=settings.postgres_pool_min_size,
        max_size=settings.postgres_pool_max_size,
        command_timeout=settings.postgres_command_timeout_seconds,
        ssl=ssl_context,
        server_settings={"application_name": "sqlserver-postgres-etl"},
    )
