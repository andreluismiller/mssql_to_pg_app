from .base import BaseProcessor
class FullReloadProcessor(BaseProcessor):
    async def run(self, obj):
        await self.loader.prepare(obj)
        _, total = await self.consume(obj, None)
        return None, total