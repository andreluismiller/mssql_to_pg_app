from datetime import datetime, timedelta
from .base import BaseProcessor

class IdIncrementalProcessor(BaseProcessor):
    async def run(self, obj):
        watermark = await self.state.get(obj.name, obj.processor.initial_value)
        if watermark is not None:
            watermark = int(watermark)
        await self.loader.prepare(obj)
        return await self.consume(obj, watermark)

class TimestampIncrementalProcessor(BaseProcessor):
    async def run(self, obj):
        watermark = await self.state.get(obj.name, obj.processor.initial_value)
        if watermark is not None:
            watermark = datetime.fromisoformat(str(watermark).replace("Z", "+00:00"))
            if obj.processor.overlap_seconds:
                watermark -= timedelta(seconds=obj.processor.overlap_seconds)
        await self.loader.prepare(obj)
        return await self.consume(obj, watermark)
