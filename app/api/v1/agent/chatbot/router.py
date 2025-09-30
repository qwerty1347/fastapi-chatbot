from fastapi import APIRouter, Query

from app.domain.agent.services.service import AgentService


router = APIRouter(prefix="/chatbot", tags=["Agent"])

ai_agent_service = AgentService()


@router.get('/')
async def index(query: str = (Query(...))):
    return await ai_agent_service.handle_agent(query)