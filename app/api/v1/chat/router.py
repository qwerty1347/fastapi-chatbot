from fastapi import APIRouter, Depends

from app.core.dependencies.chat import get_chat_agent_service
from app.services.agent.chat import ChatAgentService


router = APIRouter(prefix="/chat", tags=["Agent"])


@router.get('/')
async def index(
    query: str,
    chat_agent_service: ChatAgentService = Depends(get_chat_agent_service),
):
    await chat_agent_service.handle_agent(query)
    return {"message": "Hello AI-Agent"}
