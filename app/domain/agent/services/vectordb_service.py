import re
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, PointStruct

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
                "document_id": "category_문서 인덱스",
                "category": category,
                "doc_idx": 문서 인덱스,
                "paragraph": 청크된 인덱스,
                "doc": 문서에서 청크된 내용,
                "metadata": Document.metadata
            }

        Returns:
            None
        """
        points = []
        data = get_vectordb_data()
        splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10, separators=["\n"])

        for category, documents in data.items():
            for doc_idx, doc in enumerate(documents):
                page_content = re.sub(r'[ \t]+', ' ', doc.page_content)   # 한 줄 내 여러 개의 공백이나 탭이 연속된 경우 → 하나의 공백으로 치환
                page_content = re.sub(r'\s{2,}', '\n', page_content).strip()  # 공백문자(스페이스, 탭, 줄바꿈 등)가 2개 이상 연속된 부분을 줄바꿈(\n)으로 치환
                chunks = splitter.split_text(page_content)

                for chunk_idx, chunk in enumerate(chunks):
                    # print(f"--- chunk {chunk_idx} ---")
                    # print(chunk)
                    # print()

                    points.append(
                        PointStruct(
                            id=str(uuid.uuid4()),
                            vector=self.qdrant.embedding_model.encode(chunk).tolist(),
                            payload={
                                "document_id": f"{category}_{doc_idx}",
                                "category": category,
                                "doc_idx": doc_idx,
                                "paragraph": chunk_idx,
                                "doc": chunk,
                                "metadata": doc.metadata
                            }
                        )
                    )

        await self.qdrant.upsert_points(points)


    async def search_points(self, query: str):
        """
        입력 텍스트를 임베딩 후 유사한 포인트를 검색하는 함수입니다.
        검색 결과 중 최고 점수 포인트(top_score_point)를 기준으로 category와 doc_idx를 활용해 범위를 좁힌 후 추가 검색을 수행합니다.

        Args:
            query (str): 검색 기준이 될 벡터
            limit (int): 반환할 최대 검색 결과 개수

        Returns:
            list[ScoredPoint] | str: 검색된 포인트(ScoredPoint) 객체들의 리스트 또는 문자열
        """
        embedded_query = self.qdrant.embedding_model.encode(query).tolist()
        result = await self.handle_search_points(query, embedded_query)
        # print(f"--- result ---")
        # print(f"result: {result}")
        # print()

        return result


    async def handle_search_points(self, query: str, embedded_query):
        points = await self.qdrant.search_points(embedded_query, 10)

        if not points:
            return "답변을 생성하지 못하였습니다. 다시 시도해 주세요."

        points = self.search_keyword_point(query, points)
        top_score_points = max(points, key=lambda p: p.score)
        # print(f"--- top_score_points ---")
        # print(f"top_score_points: {top_score_point}")
        # print()
        top_score_result = await self.search_top_score_point(embedded_query, top_score_points)

        return "\n".join([p.payload['doc'] for p in top_score_result])


    def search_keyword_point(self, query, points):
        keyword_points = []

        for point in points:
            if any(keyword in query for keyword in point.payload.get('metadata')['keyword']):
                keyword_points.append(point)

        if keyword_points:
            points = keyword_points

        return points


    async def search_top_score_point(self, embedded_query, top_score_point, limit: int = 5):
        filters = Filter(
            must=[
                FieldCondition(
                    key="category",
                    match=MatchValue(value=top_score_point.payload.get("category"))
                ),
                FieldCondition(
                    key="doc_idx",
                    match=MatchValue(value=top_score_point.payload.get("doc_idx"))
                )
            ]
        )
        top_score_result = await self.qdrant.search_points(query_vector=embedded_query, limit=limit, filters=filters)

        return sorted(top_score_result, key=lambda p: p.payload['paragraph'])