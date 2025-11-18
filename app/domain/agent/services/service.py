import asyncio

from fastapi.responses import JSONResponse
from langchain import hub
from langchain.agents import AgentExecutor
from langchain.agents import create_react_agent
from langchain.agents import Tool

from app.domain.agent.modules.llm.groq import Groq
from app.domain.agent.modules.search.serp import Serp
from app.domain.agent.services.serp_service import SerpService
from app.domain.agent.services.vectordb_service import VectorDBService
from common.constants.agent.tools import ToolConstants
from common.utils.prompt import is_chitchat_prompt, set_chitchat_prompt, set_output_prompt
from common.utils.response import success_response


class AgentService:
    def __init__(self):
        self.llm = Groq()
        self.search = Serp()
        self.vector_db_service = VectorDBService()
        self.serp_service = SerpService()
        self.observations = ""
        self.tools = self.set_agent_tools()


    def set_agent_tools(self) -> list[Tool]:
        """
        에이전트 챗봇이 사용할 도구 (tool) 를 설정하는 함수입니다.

        Returns:
            list[Tool]: 에이전트의 리스트
        """
        return [
            Tool.from_function(
                name=ToolConstants.WEB_SEARCH,
                func=self.search_web,
                description=ToolConstants.descriptions[ToolConstants.WEB_SEARCH]["description"]
            ),
            Tool.from_function(
                name=ToolConstants.DB_SEARCH,
                func=self.qdrant_search,
                description=ToolConstants.descriptions[ToolConstants.DB_SEARCH]["description"]
            )
        ]


    async def handle_agent(self, user_input: str) -> JSONResponse:
        """
        사용자가 입력한 텍스트를 에이전트 챗봇이 도구를 사용하고 챗봇 답변을 생성하고 결과를 리턴하는 함수입니다.

        Args:
            user_input (str): 사용자 입력 텍스트

        Returns:
            JSONResponse: 챗봇 답변이 포함된 리턴 결과
        """
        llm_output = await asyncio.to_thread(
            self.llm.run,
            is_chitchat_prompt(user_input)
        )

        if self.is_chitchat(llm_output):
            agent_output = await asyncio.to_thread(
                self.llm.run,
                set_chitchat_prompt(user_input)
            )

        else:
            await self.set_agent(self.tools).ainvoke({"input": user_input})
            agent_output = await asyncio.to_thread(
                self.llm.run,
                set_output_prompt(user_input, self.observations)
            )

        print(f"Agent Output: {agent_output}")
        print()

        return success_response(getattr(agent_output, 'content', ''))


    def is_chitchat(self, llm_output: str) -> bool:
        """
        LLM 이 판단한 일상 대화 여부의 리턴 결과를 통해 True / False 를 지정하는 함수입니다.

        Args:
            llm_output (str): LLM 이 판단한 일상 대화 여부

        Returns:
            bool: LLM 리턴 결과 내 yes 포함된 경우 True, 그 외 False
        """
        chitchat_result = getattr(llm_output, "content", str(llm_output)).strip().lower()

        # print(f"--- chitchat ---")
        # print(f"chitchat: {chitchat_result}")
        # print()

        return "yes" in chitchat_result


    def set_agent(self, tools) -> AgentExecutor:
        """
        LLM 과 Tool 목록을 사용하여 Agent Executor를 생성하는 함수입니다.

        Args:
            tools (list[Tool]): 에이전트 챗봇에서 사용할 도구 목록

        Returns:
            AgentExecutor: 생성된 Agent Executor 인스턴스
        """
        agent = create_react_agent(
            llm=self.llm.llm,
            tools=tools,
            prompt=hub.pull("hwchase17/react"),
        )

        return AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=1,
            handle_parsing_errors=True,
        )


    def search_web(self, query: str) -> str:
        """
        Serp API를 사용하여 입력 텍스트에 대한 웹 검색 결과를 가져오고 파싱하여 리턴하는 함수입니다.

        Args:
            query (str): 검색할 텍스트 쿼리

        Returns:
            str: 웹 검색 결과를 하나의 문자열로 합쳐 반환
        """
        web_result = self.search.run(query)
        parsed_result = self.serp_service.parse_serp(web_result)
        self.observations = "\n".join(parsed_result)

        return self.observations


    def qdrant_search(self, query: str) -> str:
        """
        Qdrant Client를 사용하여 입력 텍스트의 벡터와 유사한 문서를 검색하는 함수입니다.

        Args:
            query (str): 검색할 텍스트 쿼리

        Returns:
            str: 검색된 결과를 하나의 문자열로 합쳐 반환
        """
        qdrant_result =  asyncio.run(self.vector_db_service.search_points(query))
        self.observations = qdrant_result

        return self.observations