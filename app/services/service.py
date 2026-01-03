import asyncio

from fastapi.responses import JSONResponse
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate

from app.modules.llm.groq import Groq
from app.modules.memory.short_term import ShortTermMemory
from app.modules.tool.tools import search_db, search_web
from common.constants.agent.prompt import PromptConstants
from common.utils.response import success_response


class AgentService:
    def __init__(self):
        self.llm = Groq()
        self.short_term_memory = ShortTermMemory()


    async def handle_agent(self, user_input: str) -> JSONResponse:
        """
        사용자가 입력한 텍스트를 에이전트 챗봇이 도구를 사용하고 챗봇 답변을 생성하고 결과를 리턴하는 함수입니다.

        Args:
            user_input (str): 사용자 입력 텍스트

        Returns:
            JSONResponse: llm 이 생성한 최종 답변이 포함된 리턴 결과
        """
        self.short_term_memory.buffer.append({"role": "user", "content": user_input})

        llm_chitchat_output = await asyncio.to_thread(
            self.llm.run,
            ChatPromptTemplate.from_messages([
                ("system", PromptConstants.PROMPTS['chitchat']['confirm']),
                ("user", "{input}")
            ]),
            user_input
        )

        short_term_history = self.short_term_memory.build_format_history()

        if self.is_chitchat(llm_chitchat_output):
            agent_output = await asyncio.to_thread(
                self.llm.run,
                ChatPromptTemplate.from_messages([
                    ("system", PromptConstants.PROMPTS['chitchat']['output']),
                    ("user", "{input}")
                ]),
                user_input=user_input,
                history=short_term_history
            )

        else:
            tools = [search_web, search_db]
            result = await self.set_agent(tools).ainvoke({"input": user_input})
            tool_result = [
                observation
                for action, observation in result["intermediate_steps"]
            ]

            agent_output = await asyncio.to_thread(
                self.llm.run,
                ChatPromptTemplate.from_messages([
                    ("system", PromptConstants.PROMPTS['result']['output']),
                    ("user", "질문: {input}"),
                ]),
                user_input,
                context=tool_result,
                history=short_term_history
            )

        print(f"Agent Final Answer: {agent_output}")
        print()

        agent_output = getattr(agent_output, 'content', '')
        self.short_term_memory.buffer.append({"role": "assistant", "content": agent_output})

        return success_response(agent_output)


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
        print(f"chitchat: {chitchat_result}")
        # print()

        return "yes" in chitchat_result


    def set_agent(self, tools: list, max_iterations: int = 1):
        """
        LLM 과 Tool 목록을 사용하여 Agent Executor를 생성하는 함수입니다.

        Args:
            tools (list[Tool]): 에이전트 챗봇에서 사용할 도구 목록

        Returns:
            AgentExecutor: 생성된 Agent Executor 인스턴스
        """
        react_prompt = hub.pull("hwchase17/react")
        agent = create_react_agent(
            llm=self.llm.llama,
            tools=tools,
            prompt=react_prompt
        )

        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=max_iterations,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )

        return agent_executor