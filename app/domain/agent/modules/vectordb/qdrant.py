from qdrant_client.http.models.models import ScoredPoint
from sentence_transformers import SentenceTransformer
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, SearchRequest

from config.settings import settings
from common.constants.agent.embedding_model import EmbeddingModelConstants


class Qdrant:
    def __init__(self):
        self.embedding_model = SentenceTransformer(EmbeddingModelConstants.MODELS['HuggingFace']['name'])


    async def upsert_points(self, points: list):
        qdrant = AsyncQdrantClient(url=settings.QDRANT_HOST)
        await qdrant.upsert(
            collection_name="domeggook",
            points=points,
        )


    async def search_points(self, query_vector: list, limit: int, category: str = None, doc_idx: int = None) -> list[ScoredPoint]:
        qdrant = AsyncQdrantClient(url=settings.QDRANT_HOST)
        filters = []

        if category is not None:
            filters.append(
                FieldCondition(
                    key="category",
                    match=MatchValue(value=category)
                )
            )

        if doc_idx is not None:
            filters.append(
                FieldCondition(
                    key="doc_idx",
                    match=MatchValue(value=int(doc_idx))
                )
            )

        return await qdrant.search(
            collection_name="domeggook",
            query_vector=query_vector,
            limit=limit,
            query_filter=Filter(must=filters) if filters else None
        )