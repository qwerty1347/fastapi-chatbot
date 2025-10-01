import uuid

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
                for sub_idx, item in enumerate(row):
                    points.append(
                        PointStruct(
                            id=str(uuid.uuid4()),
                            vector=self.qdrant.embedding_model.encode(item['text']).tolist(),
                            payload={
                                "document_id": f"{key}{idx}{sub_idx}",
                                "category": key,
                                "paragraph": idx,
                                "text": item['text']
                            }
                        )
                    )

        await self.qdrant.upsert_points(points)