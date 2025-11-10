import re
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.conversions.common_types import ScoredPoint
from qdrant_client.http.models import PointStruct

from app.domain.agent.modules.vectordb.qdrant import Qdrant
from storage.vectordb.data.base import get_vectordb_data


class VectorDBService:
    def __init__(self):
        self.qdrant = Qdrant()


    async def upsert_points(self):
        """
        Qdrant 벡터 DB에 임베딩 생성(문서를 벡터화하여 포인트) 업서트 하는 함수입니다.
        고유 ID와 메타데이터(payload) 를 포함한 PointStruct 객체로 생성하고 DB에 저장합니다.

        Payload 예시:
            {
                "document_id": "category_문서인덱스",
                "category": category,
                "doc_idx": 문서 인덱스,
                "paragraph": 청크된 단락 인덱스,
                "doc": 실제 문서 내용 중 청크된 내용
            }

        Returns:
            None
        """
        points = []
        data = get_vectordb_data()
        splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10, separators=["\n"])

        for category, documents in data.items():
            for doc_idx, doc in enumerate(documents):
                doc = re.sub(r'[ \t]+', ' ', doc)   # 한 줄 내 여러 개의 공백이나 탭이 연속된 경우 → 하나의 공백으로 치환
                doc = re.sub(r'\s{2,}', '\n', doc).strip()  # 공백문자(스페이스, 탭, 줄바꿈 등)가 2개 이상 연속된 부분을 줄바꿈(\n)으로 치환

                chunks = splitter.split_text(doc.strip())

                for chunk_idx, chunk in enumerate(chunks):
                    points.append(
                        PointStruct(
                            id=str(uuid.uuid4()),
                            vector=self.qdrant.embedding_model.encode(chunk).tolist(),
                            payload={
                                "document_id": f"{category}_{doc_idx}",
                                "category": category,
                                "doc_idx": doc_idx,
                                "paragraph": chunk_idx,
                                "doc": chunk
                            }
                        )
                    )

        await self.qdrant.upsert_points(points)


    async def handle_points(self, query) -> list[ScoredPoint]:
        """
        입력한 텍스트를 기반으로 벡터에 대한 유사한 포인트를 검색하고 paragraph 순으로 정렬하여 리스트로 반환하는 함수입니다.

        Args:
            query (str): 검색할 텍스트 쿼리.

        Returns:
            list[ScoredPoint]: paragraph 순으로 정렬된 검색 결과 포인트 리스트.
        """
        results = await self.search_points(query)
        return sorted(results, key=lambda p: p.payload['paragraph'])


    async def search_points(self, query: str, limit: int = 15) -> list[ScoredPoint]:
        """
        입력 텍스트를 임베딩으로 변환하여 Qdrant 에서 유사한 포인트를 검색하는 함수입니다.
        검색 결과 중 최고 점수 포인트(top_score_point)를 기준으로 category와 doc_idx를 활용해 범위를 좁힌 후 추가 검색을 수행합니다.

        Args:
            query (str): 검색 기준이 될 벡터
            limit (int): 반환할 최대 검색 결과 개수

        Returns:
            list[ScoredPoint]: 검색된 포인트(ScoredPoint) 객체들의 리스트
        """
        embedded_query = self.qdrant.embedding_model.encode(query).tolist()
        results: list[ScoredPoint] = await self.qdrant.search_points(embedded_query, limit)
        top_score_point: ScoredPoint = max(results, key=lambda p: p.score)

        return await self.qdrant.search_points(
            embedded_query,
            3,
            category=top_score_point.payload.get("category"),
            doc_idx=top_score_point.payload.get("doc_idx"),
        )