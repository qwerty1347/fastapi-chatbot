from fastapi import APIRouter

from app.domain.ai_agent.services.service import AiAgentService


router = APIRouter(prefix="/ai-agent", tags=["AI-Agent"])

ai_agent_service = AiAgentService()


@router.get("/")
async def root():
    return {"message": "Hello AI-Agent"}



@router.get('/test')
async def test():
    await ai_agent_service.handle_ai_agent()
    return {"message": "Hello handle_ai_agent"}

