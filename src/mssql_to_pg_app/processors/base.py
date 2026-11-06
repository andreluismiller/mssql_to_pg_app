import asyncio
from mssql_to_pg_app.extractors.sqlserver import END, Batch, ProducerError

class BaseProcessor:
    def __init__(self, extractor, loader, state, queue_max_batches: int):
        self.extractor, self.loader, self.state = extractor, loader, state
        self.queue_max_batches = queue_max_batches

    async def consume(self, obj, watermark):
        queue: asyncio.Queue = asyncio.Queue(maxsize=self.queue_max_batches)
        loop = asyncio.get_running_loop()
        producer = asyncio.create_task(
            asyncio.to_thread(self.extractor.produce, obj, watermark, queue, loop)
        )
        total = 0
        maximum = watermark
        try:
            while True:
                item = await queue.get()
                if item is END:
                    break
                if isinstance(item, ProducerError):
                    raise item.error
                assert isinstance(item, Batch)
                total += await self.loader.load(obj, item.columns, item.rows)
                if obj.processor.watermark_column:
                    index = item.columns.index(obj.processor.watermark_column)
                    values = [row[index] for row in item.rows if row[index] is not None]
                    if values:
                        maximum = max(values) if maximum is None else max(maximum, max(values))
        finally:
            await producer
        return maximum, total
