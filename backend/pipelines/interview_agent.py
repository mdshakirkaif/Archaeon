from .retrieval import RetrievalPipeline


class InterviewAgentPipeline:
    def __init__(self) -> None:
        self.retrieval = RetrievalPipeline()

    async def run(self, query: str) -> dict:
        documents = await self.retrieval.search(query)
        return {"query": query, "documents": documents}
