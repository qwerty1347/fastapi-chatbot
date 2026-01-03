from langchain.tools import tool

from app.modules.tool.db_search import DBSearch
from app.modules.tool.web_search import WebSearch


web_search = WebSearch()
db_search = DBSearch()


@tool
def search_web(query: str):
    """도매꾹을 제외한 정보 검색에 사용. 질문에 '도매꾹'이 포함되어 있지 않다면 항상 사용할 것"""
    result = web_search.search_serp(query)
    return result

@tool
def search_db(query: str):
    """도매꾹과 관련된 모든 정보 검색에 사용. 질문에 '도매꾹'이 포함되어 있다면 항상 사용할 것"""
    result = db_search.search_qdrant(query)
    return result
