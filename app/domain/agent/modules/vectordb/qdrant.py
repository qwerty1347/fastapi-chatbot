from qdrant_client import AsyncQdrantClient
from sentence_transformers import SentenceTransformer

from common.constants.embedding_model import EmbeddingModelConstants
from config.settings import settings


class Qdrant:
    def __init__(self):
        self.qdrant = AsyncQdrantClient(url=settings.QDRANT_HOST)
        self.embedding_model = SentenceTransformer(EmbeddingModelConstants.MODELS['HuggingFace']['name'])


    async def upsert_points(self, points: list):
        scroll_resp  = await self.qdrant.upsert(
            collection_name="domeggook",
            points=points,
        )