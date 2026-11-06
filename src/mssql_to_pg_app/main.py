from contextlib import asynccontextmanager
from mssql_to_pg_app.database.postgres import create_pool
from mssql_to_pg_app.extractors.sqlserver import SqlServerExtractor
from mssql_to_pg_app.loaders.postgres import AsyncPostgresLoader
from mssql_to_pg_app.state.postgres import AsyncStateStore
from mssql_to_pg_app.orchestration.runner import AsyncRunner

@asynccontextmanager
async def runtime(config):
    pool = await create_pool(config.app)
    try:
        state = AsyncStateStore(pool, config.app.state_schema, config.app.state_table)
        await state.initialize()
        extractor = SqlServerExtractor(config.app.fetch_size, config.source.command_timeout_seconds)
        loader = AsyncPostgresLoader(pool, config.target.staging_schema)
        yield AsyncRunner(extractor, loader, state, config.app)
    finally:
        await pool.close()
