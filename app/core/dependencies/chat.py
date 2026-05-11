from fastapi import Depends
from sentence_transformers import SentenceTransformer

from app.core.dependencies.common import get_embedding_model, get_groq, get_qdrant
from app.infrastructure.vectordb.qdrant import Qdrant
from app.modules.llm.groq import Groq
from app.services.agent.chat import ChatAgentService


def get_chat_agent_service(
    qdrant: Qdrant = Depends(get_qdrant),
    embedding_model: SentenceTransformer = Depends(get_embedding_model),
    llm: Groq = Depends(get_groq),
) -> ChatAgentService:
    return ChatAgentService(qdrant, embedding_model, llm)