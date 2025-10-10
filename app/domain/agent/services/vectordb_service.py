import uuid

from collections import defaultdict
from qdrant_client.http.models import PointStruct

from app.domain.agent.modules.vectordb.qdrant import Qdrant
from storage.vectordb.data.base import get_vectordb_data


class VectorDBService:
    def __init__(self):
        self.qdrant = Qdrant()


    async def upsert_points(self):
        points = []
        data = get_vectordb_data()

        for category, documents in data.items():  # category = "notice", "api" 등
            for doc_idx, doc in enumerate(documents):
                for key, value in doc.items():  # key = "제목", "본문", "변경_내용" 등
                    if isinstance(value, list):
                        for sec_idx, item in enumerate(value):
                            points.append(
                                PointStruct(
                                    id=str(uuid.uuid4()),
                                    vector=self.qdrant.embedding_model.encode(item).tolist(),
                                    payload={
                                        "document_id": f"{category}_{doc_idx}",
                                        "doc_idx": doc_idx,
                                        "category": category,
                                        "section": key,
                                        "paragraph": sec_idx,
                                        "text": item
                                    }
                                )
                            )
                    else:
                        points.append(
                            PointStruct(
                                id=str(uuid.uuid4()),
                                vector=self.qdrant.embedding_model.encode(value).tolist(),
                                payload={
                                    "document_id": f"{category}_{doc_idx}",
                                    "doc_idx": doc_idx,
                                    "category": category,
                                    "section": key,
                                    "paragraph": 0,
                                    "text": value
                                }
                            )
                        )

        await self.qdrant.upsert_points(points)

    async def search_points(self, query: str, limit: int = 10):
        return await self.qdrant.search_points(self.qdrant.embedding_model.encode(query).tolist(), limit)


    def merge_points_by_paragraph(self, results: list):
        if not results:
            return []

        # 최고 점수 포인트 기준 category
        best_point = max(results, key=lambda p: p.score)
        best_point_category = best_point.payload.get("category")

        grouped = defaultdict(list)
        scores = {}

        for point in results:
            if point.payload.get("category") != best_point_category:
                continue  # 다른 category는 무시

            doc_id = point.payload.get("document_id")
            paragraph = point.payload.get("paragraph")
            key = (doc_id, paragraph)

            grouped[key].append(point.payload.get("text"))

            # 문단 최고 점수
            if key not in scores or point.score > scores[key]:
                scores[key] = point.score

        # 결과 리스트 생성
        answers = [
            {
                "document_id": doc_id,
                "paragraph": paragraph,
                "text": " ".join(texts),
                "score": scores[(doc_id, paragraph)]
            }
            for (doc_id, paragraph), texts in grouped.items()
        ]

        answers.sort(key=lambda x: x["score"], reverse=True)


        print("=====================")
        print(answers)
        print("=====================")

        return answers