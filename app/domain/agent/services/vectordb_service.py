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

        for index, (key, value) in enumerate(data.items()):
            for idx, row in enumerate(value):
                for sub_idx, sub_row in enumerate(row):
                    points.append(
                        PointStruct(
                            id=str(uuid.uuid4()),
                            vector=self.qdrant.embedding_model.encode(sub_row).tolist(),
                            payload={
                                "document_id": f"{key}{idx}{sub_idx}",
                                "category": key,
                                "paragraph": idx,
                                "text": sub_row
                            }
                        )
                    )

        await self.qdrant.upsert_points(points)


    async def search_points(self, query: str, limit: int = 10):
        return await self.qdrant.search_points(self.qdrant.embedding_model.encode(query).tolist(), limit)


    def merge_points_by_paragraph(self, results: list):
        grouped = defaultdict(list)
        scores = {}

        for point in results:
            doc_id = point.payload.get("document_id")
            paragraph = point.payload.get("paragraph")
            key = (doc_id, paragraph)
            grouped[key].append(point.payload.get("text"))

            # 문단의 최고 점수를 저장
            if key not in scores or point.score > scores[key]:
                scores[key] = point.score

        answers = []

        for (doc_id, paragraph), texts in grouped.items():
            answers.append({
                "document_id": doc_id,
                "paragraph": paragraph,
                "text": " ".join(texts),  # 같은 문단의 텍스트 합치기
                "score": scores[(doc_id, paragraph)]
            })

        answers.sort(key=lambda x: x["score"], reverse=True)

        return answers