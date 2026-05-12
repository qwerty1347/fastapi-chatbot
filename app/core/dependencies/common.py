from fastapi import Depends
from functools import lru_cache
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from app.core.config import config
from app.infrastructure.vectordb.qdrant import Qdrant
from app.modules.llm.groq import Groq
from config.embedding_model import EmbeddingModel


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=config.QDRANT_HOST)


@lru_cache(maxsize=1)
def get_embedding_model()-> SentenceTransformer:
    return SentenceTransformer(EmbeddingModel.MODELS['hugging_face']['sentence_transformer']['All-MiniLM-L6-v2']['name'])


@lru_cache(maxsize=1)
def get_groq():
    return Groq()


def get_qdrant(client: QdrantClient = Depends(get_qdrant_client)) -> Qdrant:
    return Qdrant(client)