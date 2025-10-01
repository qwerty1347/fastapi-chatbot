from fastapi import APIRouter

from app.domain.agent.services.vectordb_service import VectorDBService


router = APIRouter(prefix="/vector", tags=["VectorDB"])
vectordb_service = VectorDBService()


@router.get("/embeddings")
async def index():
    await vectordb_service.upsert_points()
    return {"message": "Hello Vector"}