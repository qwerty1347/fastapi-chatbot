import asyncio

from app.domain.agent.services.vectordb_service import VectorDBService


class DBSearch:
    def __init__(self):
        pass


    def search_qdrant(self, query: str):
        """
        Qdrant Client를 사용하여 입력 텍스트의 벡터와 유사한 문서를 검색하는 함수입니다.

        Args:
            query (str): 검색할 텍스트 쿼리

        Returns:
            str: 검색된 결과를 하나의 문자열로 합쳐 반환
        """
        qdrant_service = VectorDBService()
        return asyncio.run(qdrant_service.search_points(query))