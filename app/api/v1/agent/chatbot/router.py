from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.services.service import AgentService


router = APIRouter(prefix="/chatbot", tags=["Agent"])
agent_service = AgentService()


@router.get('/')
async def index(query: str = (Query(...))) -> JSONResponse:
    return await agent_service.handle_agent(query)