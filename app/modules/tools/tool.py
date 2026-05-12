from langchain.tools import BaseTool
from langchain_core.tools import tool

from app.modules.tools.db_search import DBSearch
from app.modules.tools.web_search import WebSearch


def build_db_search(db_search: DBSearch) -> BaseTool:
    @tool
    def use_db_tool(query: str) -> str:
        """도매꾹과 관련된 모든 정보 검색에 사용."""
        return db_search.search_qdrant(query)
    return use_db_tool


def build_web_search(web_search: WebSearch) -> BaseTool:
    @tool
    def use_web_tool(query: str) -> str:
        """도매꾹을 제외한 정보 검색에 사용."""
        return web_search.search_serp(query)
    return use_web_tool