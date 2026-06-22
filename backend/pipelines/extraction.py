from typing import Any


class ExtractionPipeline:
    async def extract(self, text: str) -> dict[str, Any]:
        return {"text": text, "entities": [], "summary": text[:200]}
