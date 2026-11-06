import asyncio
import structlog
from mssql_to_pg_app.processors import PROCESSORS
log = structlog.get_logger()

class AsyncRunner:
    def __init__(self, extractor, loader, state, settings):
        self.extractor, self.loader, self.state, self.settings = extractor, loader, state, settings
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_objects)

    async def run_one(self, obj):
        async with self.semaphore:
            await self.state.start(obj.name)
            try:
                processor = PROCESSORS[obj.processor.type](
                    self.extractor, self.loader, self.state, self.settings.queue_max_batches
                )
                watermark, rows = await processor.run(obj)
                await self.state.success(obj.name, watermark, rows)
                log.info("object_complete", object=obj.name, rows=rows, watermark=str(watermark))
                return rows
            except Exception as exc:
                await self.state.failure(obj.name, exc)
                log.exception("object_failed", object=obj.name)
                raise

    async def run_all(self, objects):
        results = await asyncio.gather(
            *(self.run_one(obj) for obj in objects), return_exceptions=not self.settings.fail_fast
        )
        failures = [result for result in results if isinstance(result, Exception)]
        if failures:
            raise RuntimeError(f"{len(failures)} object(s) failed")
