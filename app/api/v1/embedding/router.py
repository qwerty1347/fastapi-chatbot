from fastapi import APIRouter

from app.services.vectordb_service import VectorDBService
from common.utils.response import success_response


router = APIRouter(prefix="/embedding", tags=["VectorDB"])
vectordb_service = VectorDBService()


@router.get("/")
async def index():
    await vectordb_service.create_points_from_documents()
    return success_response()