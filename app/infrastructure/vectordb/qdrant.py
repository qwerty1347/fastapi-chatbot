from qdrant_client import QdrantClient


class Qdrant:
    def __init__(self, client: QdrantClient):
        self.qdrant = client


    def upsert_points(self, collection_name: str, points: list):
        self.qdrant.upsert(
            collection_name=collection_name,
            points=points
        )


    def find_points(self, collection_name: str, query_vector: list, limit: int):
        response = self.qdrant.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit
        )

        return response.points