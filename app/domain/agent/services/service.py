import asyncio

from langchain import hub
from langchain.agents import AgentExecutor
from langchain.agents import create_react_agent
from langchain.agents import Tool

from app.domain.agent.modules.llm.groq import Groq
from app.domain.agent.modules.search.serp import Serp
from common.utils.prompt import set_output_prompt


class AgentService:
    def __init__(self):
        self.llm = Groq()
        self.search = Serp()
        self.observations = []
        self.tools = self.set_agent_tools()


    def set_agent_tools(self):
        return [
            Tool.from_function(
                name="WEB_SEARCH",
                func=self.search_web,
                description="최신 정보 등 정확한 정보가 필요할 경우 사용"
            ),
            Tool.from_function(
                name="QDRANT_SEARCH",
                func=self.qdrant_search,
                description="회사 정보, 회사 내부 문서 등 정보가 필요할 경우 사용"
            )
        ]


    async def handle_agent(self, user_input: str) -> dict:
        self.observations = []

        await self.set_agent(self.tools).ainvoke({"input": user_input})
        agent_output = await asyncio.to_thread(
            self.llm.run,
            set_output_prompt(user_input, self.observations)
        )
        print("Agent Output: ", agent_output)

        return {
            "agent_output": getattr(agent_output, 'content', '')
        }


    def set_agent(self, tools):
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
        results = self.search.run(query)
        obs = " ".join(results)
        self.observations.append(obs)
        return obs


    def qdrant_search(self, query: str) -> str:
        obs = f"Qdrant 검색 결과: {query} 관련 데이터."
        self.observations.append(obs)
        return obs