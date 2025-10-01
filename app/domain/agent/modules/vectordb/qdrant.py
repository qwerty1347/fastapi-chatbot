from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from common.constants.embedding_model import EmbeddingModelConstants
from config.settings import settings


class Qdrant:
    def __init__(self):
        self.qdrant = QdrantClient(url=settings.QDRANT_HOST)
        self.embedding_model = SentenceTransformer(EmbeddingModelConstants.MODELS['HuggingFace']['name'])
