from fastapi import Depends
from langchain_core.tools.base import BaseTool

from app.core.dependencies.common import get_embedding_model, get_groq, get_qdrant
from app.modules.llm.groq import Groq
from app.modules.search.serp import Serp
from app.modules.tools.db_search import DBSearch
from app.modules.tools.tool import build_db_search, build_web_search
from app.modules.tools.web_search import WebSearch
from app.services.agent.chat import ChatAgentService


def get_serp() -> Serp:
    return Serp()


def get_db_search(
    qdrant=Depends(get_qdrant),
    embedding_model=Depends(get_embedding_model)
) -> DBSearch:
    return DBSearch(qdrant, embedding_model)


def get_web_search(
    serp: Serp = Depends(get_serp),
) -> WebSearch:
    return WebSearch(serp)


def get_chat_agent_tools(
    db_search: DBSearch = Depends(get_db_search),
    web_search: WebSearch = Depends(get_web_search),
) -> list[BaseTool]:
    return [build_db_search(db_search), build_web_search(web_search)]


def get_chat_agent_service(
    agent_tools = Depends(get_chat_agent_tools),
    llm: Groq = Depends(get_groq),
) -> ChatAgentService:
    return ChatAgentService(agent_tools, llm)