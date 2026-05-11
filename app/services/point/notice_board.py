import re
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer

from app.infrastructure.storage.board import get_board_notices
from app.infrastructure.vectordb.qdrant import Qdrant


class NoticeBoardPointService:
    def __init__(self, qdrant: Qdrant, embedding_model: SentenceTransformer):
        self.qdrant = qdrant
        self.embedding_model = embedding_model


    def embed_notice_board(self):
        board_notices = get_board_notices()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10, separators=["\n"])
        points = []

        for notices in board_notices.values():
            for doc_idx, document in enumerate(notices):
                page_content = self.preprocess_text(document.page_content)
                chunks = text_splitter.split_text(page_content)

                for chunk_idx, chunk in enumerate(chunks):
                    points.append(
                        PointStruct(
                            id=str(uuid.uuid4()),
                            vector=self.embedding_model.encode(chunk).tolist(),
                            payload={
                                "document_id": f"notice_{doc_idx}",
                                "category": "notice",
                                "doc_idx": doc_idx,
                                "paragraph": chunk_idx,
                                "doc": chunk,
                                "metadata": document.metadata
                            }
                        )
                    )

        self.qdrant.upsert_points("board_notice", points)


    def preprocess_text(self, text):
        normalized_space = re.sub(r'[ \t]+', ' ', text)  # 한 줄 내 여러 개의 공백이나 탭이 연속된 경우 → 하나의 공백으로 치환
        normalized_linebreak = re.sub(r'\s{2,}', '\n', normalized_space).strip()  # 공백문자(스페이스, 탭, 줄바꿈 등)가 2개 이상 연속된 부분을 줄바꿈(\n)으로 치환

        return normalized_linebreak