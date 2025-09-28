from fastapi import APIRouter, Query

from app.domain.agent.services.service import AgentService


router = APIRouter(prefix="/chatbot", tags=["Agent"])

ai_agent_service = AgentService()


@router.get("/")
async def index():
    return {"message": "Hello AI-Agent"}


@router.get('/test')
async def test(query: str = (Query(...))):
    return ai_agent_service.handle_ai_agent(query)