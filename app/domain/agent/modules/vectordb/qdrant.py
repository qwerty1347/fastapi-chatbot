from qdrant_client.http.models.models import ScoredPoint
from sentence_transformers import SentenceTransformer
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

from config.settings import settings
from common.constants.agent.embedding_model import EmbeddingModelConstants


class Qdrant:
    def __init__(self):
        self.embedding_model = SentenceTransformer(EmbeddingModelConstants.MODELS['HuggingFace']['name'])


    async def upsert_points(self, points: list):
        """
        Qdrant Client를 사용하여 입력 점을 업데이트하는 함수입니다.

        Args:
            points (list): 업데이트할 데이터 (벡터 + 메타데이터)

        Returns:
            None
        """
        qdrant = AsyncQdrantClient(url=settings.QDRANT_HOST)

        await qdrant.upsert(
            collection_name="domeggook",
            points=points,
        )


    async def search_points(self, query_vector: list, limit: int, filters = None) -> list[ScoredPoint]:
    # async def search_points(self, query_vector: list, limit: int, category: str = None, doc_idx: int = None) -> list[ScoredPoint]:
        """
        Qdrant Client를 사용하여 입력 벡터에 대한 유사한 포인트를 검색하는 함수입니다.

        Args:
            query_vector (list): 검색 기준이 될 벡터
            limit (int): 반환할 최대 검색 결과 개수
            category (str, optional): 특정 카테고리 검색 범위를 제한할 때 사용. Defaults to None.
            doc_idx (int, optional): 특정 문서 인덱스로 검색 범위를 제한할 때 사용. Defaults to None.

        Returns:
            list[ScoredPoint]: 검색된 포인트(ScoredPoint) 객체들의 리스트
        """
        qdrant = AsyncQdrantClient(url=settings.QDRANT_HOST)

        return await qdrant.search(
            collection_name="domeggook",
            query_vector=query_vector,
            limit=limit,
            query_filter=filters if filters else None
        )