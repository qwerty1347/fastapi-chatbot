import uuid

from qdrant_client.conversions.common_types import ScoredPoint
from qdrant_client.http.models import PointStruct

from app.domain.agent.modules.vectordb.qdrant import Qdrant
from storage.vectordb.data.base import get_vectordb_data


class VectorDBService:
    def __init__(self):
        self.qdrant = Qdrant()


    async def upsert_points(self):
        points = []
        data = get_vectordb_data()

        for category, documents in data.items():
            for doc_idx, doc in enumerate(documents):

                if isinstance(doc, (tuple, list)):
                    items = doc
                else:
                    items = [doc]

                for sec_idx, item in enumerate(items):
                    vector = self.qdrant.embedding_model.encode(item).tolist()

                    points.append(
                        PointStruct(
                            id=str(uuid.uuid4()),
                            vector=vector,
                            payload={
                                "document_id": f"{category}_{doc_idx}",
                                "category": category,
                                "doc_idx": doc_idx,
                                "paragraph": sec_idx,
                                "doc": item
                            }
                        )
                    )

        await self.qdrant.upsert_points(points)


    async def handle_points(self, query) -> list[ScoredPoint]:
        results = await self.search_points(query)
        return sorted(results, key=lambda p: p.payload['paragraph'])


    async def search_points(self, query: str, limit: int = 10) -> list[ScoredPoint]:
        results: list[ScoredPoint] = await self.qdrant.search_points(self.qdrant.embedding_model.encode(query).tolist(), limit)
        top_score_point: ScoredPoint = max(results, key=lambda p: p.score)

        return await self.qdrant.search_points(
            self.qdrant.embedding_model.encode(query).tolist(),
            limit,
            category=top_score_point.payload.get("category"),
            doc_idx=top_score_point.payload.get("doc_idx"),
        )