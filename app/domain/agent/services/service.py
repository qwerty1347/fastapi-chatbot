import asyncio

from langchain import hub
from langchain.agents import AgentExecutor
from langchain.agents import create_react_agent
from langchain.agents import Tool

from app.domain.agent.modules.llm.groq import Groq
from app.domain.agent.modules.search.serp import Serp
from app.domain.agent.services.vectordb_service import VectorDBService
from common.constants.agent.tools import ToolConstants
from common.utils.prompt import set_output_prompt


class AgentService:
    def __init__(self):
        self.llm = Groq()
        self.search = Serp()
        self.vector_db_service = VectorDBService()
        self.observations = []
        self.tools = self.set_agent_tools()


    def set_agent_tools(self):
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
        results =  asyncio.run(self.vector_db_service.search_points(query))
        answers = self.vector_db_service.merge_points_by_paragraph(results)
        obs = " ".join([item['text'] for item in answers])
        self.observations.append(obs)
        return obs