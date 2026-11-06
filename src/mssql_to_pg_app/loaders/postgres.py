from uuid import uuid4
import asyncpg
from mssql_to_pg_app.sql import pg_quote

class AsyncPostgresLoader:
    def __init__(self, pool: asyncpg.Pool, staging_schema: str):
        self.pool = pool
        self.staging_schema = staging_schema

    async def prepare(self, obj) -> None:
        async with self.pool.acquire() as connection:
            await connection.execute(f"CREATE SCHEMA IF NOT EXISTS {pg_quote(obj.target.schema_name)}")
            await connection.execute(f"CREATE SCHEMA IF NOT EXISTS {pg_quote(self.staging_schema)}")
            if obj.target.mode == "replace":
                await connection.execute(
                    f"TRUNCATE TABLE {pg_quote(obj.target.schema_name)}.{pg_quote(obj.target.object)}"
                )

    async def load(self, obj, source_columns: list[str], rows: list[tuple]) -> int:
        if not rows:
            return 0
        target_columns = [obj.target.column_map.get(name, name) for name in source_columns]
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                if obj.target.mode == "upsert":
                    await self._upsert(connection, obj, target_columns, rows)
                else:
                    await connection.copy_records_to_table(
                        table_name=obj.target.object,
                        schema_name=obj.target.schema_name,
                        records=rows,
                        columns=target_columns,
                    )
        return len(rows)

    async def _upsert(self, connection, obj, columns: list[str], rows: list[tuple]) -> None:
        stage = f"_etl_{obj.target.object}_{uuid4().hex[:10]}"
        target = f"{pg_quote(obj.target.schema_name)}.{pg_quote(obj.target.object)}"
        await connection.execute(
            f"CREATE TEMP TABLE {pg_quote(stage)} (LIKE {target} INCLUDING DEFAULTS) ON COMMIT DROP"
        )
        await connection.copy_records_to_table(stage, records=rows, columns=columns)
        column_sql = ", ".join(pg_quote(name) for name in columns)
        key_sql = ", ".join(pg_quote(name) for name in obj.target.primary_key)
        updates = ", ".join(
            f"{pg_quote(name)} = EXCLUDED.{pg_quote(name)}"
            for name in columns if name not in obj.target.primary_key
        )
        action = f"DO UPDATE SET {updates}" if updates else "DO NOTHING"
        await connection.execute(
            f"INSERT INTO {target} ({column_sql}) SELECT {column_sql} FROM {pg_quote(stage)} "
            f"ON CONFLICT ({key_sql}) {action}"
        )
