import asyncio
from dataclasses import dataclass
from typing import Any
from mssql_to_pg_app.database.sqlserver import connect
from mssql_to_pg_app.sql import source_select

@dataclass(slots=True)
class Batch:
    columns: list[str]
    rows: list[tuple[Any, ...]]

@dataclass(slots=True)
class ProducerError:
    error: Exception

END = object()

class SqlServerExtractor:
    def __init__(self, fetch_size: int, command_timeout_seconds: int):
        self.fetch_size = fetch_size
        self.command_timeout_seconds = command_timeout_seconds

    def produce(self, obj, watermark, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop) -> None:
        try:
            sql, params = source_select(obj, watermark)
            with connect() as connection:
                cursor = connection.cursor()
                cursor.timeout = self.command_timeout_seconds
                cursor.execute(sql, params)
                columns = [item[0] for item in cursor.description]
                while rows := cursor.fetchmany(self.fetch_size):
                    future = asyncio.run_coroutine_threadsafe(
                        queue.put(Batch(columns=columns, rows=[tuple(row) for row in rows])), loop
                    )
                    future.result()
        except Exception as exc:
            asyncio.run_coroutine_threadsafe(queue.put(ProducerError(exc)), loop).result()
        finally:
            asyncio.run_coroutine_threadsafe(queue.put(END), loop).result()
