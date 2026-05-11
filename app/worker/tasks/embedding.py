from app.core.dependencies.common import get_embedding_model, get_qdrant_client
from app.infrastructure.vectordb.qdrant import Qdrant
from app.services.point.notice_board import NoticeBoardPointService
from app.worker.celery_app import celery


@celery.task
def embed_notice_board():
    notice_board_service = NoticeBoardPointService(
        qdrant=Qdrant(get_qdrant_client()),
        embedding_model=get_embedding_model()
    )

    notice_board_service.embed_notice_board()

    return True