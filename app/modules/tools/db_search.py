from sentence_transformers import SentenceTransformer

from app.infrastructure.vectordb.qdrant import Qdrant


class DBSearch:
    def __init__(self, qdrant: Qdrant, embedding_model: SentenceTransformer):
        self.qdrant = qdrant
        self.embedding_model = embedding_model


    def search_qdrant(self, query: str) -> str:
        """
        Qdrant Client를 사용하여 입력 텍스트의 벡터와 유사한 문서를 검색하는 함수입니다.

        Args:
            query (str): 검색할 텍스트 쿼리

        Returns:
            str: 검색된 결과를 하나의 문자열로 합쳐 반환
        """
        vector = self.embedding_model.encode(query).tolist()
        points = self.qdrant.find_points(
            collection_name="board_notice",
            query_vector=vector,
            limit=5,
        )

        if not points:
            return "답변을 생성하지 못하였습니다."

        return "\n".join(p.payload.get("doc", "") for p in points)
