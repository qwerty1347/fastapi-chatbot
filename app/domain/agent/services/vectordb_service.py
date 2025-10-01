from app.domain.agent.modules.vectordb.qdrant import Qdrant
from storage.vectordb.data.base import get_vectordb_data


class VectorDBService:
    def __init__(self):
        self.vectordb_data = get_vectordb_data()
        pass


    async def upsert_points(self):
        qdrant = Qdrant()
        print(self.vectordb_data)
        pass
