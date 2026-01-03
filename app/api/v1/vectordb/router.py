from fastapi import APIRouter

from app.services.vectordb_service import VectorDBService
from common.utils.response import success_response


router = APIRouter(prefix="/vector", tags=["VectorDB"])
vectordb_service = VectorDBService()


@router.get("/embeddings")
async def index():
    await vectordb_service.create_points_from_data()
    return success_response()