from fastapi import APIRouter, Depends

from app.core.dependencies.chat import get_chat_agent_service
from app.core.utils.response import success_response
from app.schemas.chat.request import ChatAgentRequest
from app.services.agent.chat import ChatAgentService


router = APIRouter(prefix="/chat", tags=["Agent"])

@router.post('/')
async def index(
    body: ChatAgentRequest,
    chat_agent_service: ChatAgentService = Depends(get_chat_agent_service),
):
    agent_output = await chat_agent_service.run_chat_agent(body.query)
    return success_response(agent_output)