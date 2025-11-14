import re
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.conversions.common_types import ScoredPoint
from qdrant_client.http.models import Filter, FieldCondition, MatchText, MatchValue, PointStruct

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
                    # print(f"--- Chunk {chunk_idx} ---")
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


    async def search_points(self, query: str) -> list[ScoredPoint]:
        """
        입력 텍스트를 임베딩 후 유사한 포인트를 검색하는 함수입니다.
        검색 결과 중 최고 점수 포인트(top_score_point)를 기준으로 category와 doc_idx를 활용해 범위를 좁힌 후 추가 검색을 수행합니다.

        Args:
            query (str): 검색 기준이 될 벡터
            limit (int): 반환할 최대 검색 결과 개수

        Returns:
            list[ScoredPoint]: 검색된 포인트(ScoredPoint) 객체들의 리스트
        """
        embedded_query = self.qdrant.embedding_model.encode(query).tolist()
        # results: list[ScoredPoint] = await self.qdrant.search_points(embedded_query, 10)
        results = await self.test(query, embedded_query)

        print("search_point", results)



        return results



        """ top_score_point: ScoredPoint = max(results, key=lambda p: p.score)



        results = await self.qdrant.search_points(
            embedded_query,
            3,
            category=top_score_point.payload.get("category"),
            doc_idx=top_score_point.payload.get("doc_idx"),
        )

        return sorted(results, key=lambda p: p.payload['paragraph']) """


    async def test(self, query: str, embedded_query):
        points = await self.qdrant.search_points(embedded_query, 10)

        for point in points:
            keywords = point.payload.get("metadata")['keyword']

            normalized_query = query.replace(" ", "")

            print(normalized_query)

            if any(keyword in normalized_query for keyword in keywords):
                print(1, keywords)
                print()

            print(2, keywords)







        top_score_point: ScoredPoint = max(points, key=lambda p: p.score)


        return top_score_point