from langchain_core.tools import tool
from sentence_transformers import SentenceTransformer

from app.infrastructure.vectordb.qdrant import Qdrant
from app.modules.tools.db_search import DBSearch
from app.modules.tools.web_search import WebSearch


def get_tools(qdrant: Qdrant, embedding_model: SentenceTransformer):
    db_search = DBSearch(qdrant, embedding_model)
    web_search = WebSearch()

    @tool
    def search_db_tool(query: str):
        """도매꾹과 관련된 모든 정보 검색에 사용."""
        return db_search.search_qdrant(query)

    @tool
    def search_web_tool(query: str):
        """도매꾹을 제외한 정보 검색에 사용."""
        return web_search.search_serp(query)

    return [search_web_tool, search_db_tool]