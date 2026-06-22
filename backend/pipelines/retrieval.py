from typing import Any


class RetrievalPipeline:
    async def search(self, query: str) -> list[dict[str, Any]]:
        return [{"id": 1, "title": "Example result", "snippet": f"Search results for {query}"}]
