from sentence_transformers import SentenceTransformer
from qdrant_client import AsyncQdrantClient

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


    async def search_points(self, query_vector: list, limit: int):
        qdrant = AsyncQdrantClient(url=settings.QDRANT_HOST)
        return await qdrant.search(
            collection_name="domeggook",
            query_vector=query_vector,
            limit=limit
        )