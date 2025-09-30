from fastapi import APIRouter
from app.api.v1.agent.chatbot.router import router as chatbot_router


router = APIRouter(prefix="/agent")

router.include_router(chatbot_router)



@router.get("/")
async def root():
    return {"message": "Hello AI-Agent"}