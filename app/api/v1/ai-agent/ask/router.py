from fastapi import APIRouter


router = APIRouter(prefix="/ai-agent/ask", tags=["AI-Agent"])

@router.get('/')
async def index():
    return {"message": "Hello AI-Agent!"}
