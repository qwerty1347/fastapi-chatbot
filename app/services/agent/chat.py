import asyncio
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import BaseTool

from app.modules.llm.groq import Groq
from app.modules.memory.short_term import ShortTermMemory
from app.modules.prompt.chat import CHAT_PROMPTS


# hub.pull 은 네트워크/디스크 I/O 가 있을 수 있으므로 모듈 로드 시 1회만 호출.
REACT_PROMPT = hub.pull("hwchase17/react")


class ChatAgentService:
    def __init__(self, agent_tools: list[BaseTool], llm: Groq, max_iterations: int = 1):
        self.agent_tools = agent_tools
        self.llm = llm
        self.short_term_memory = ShortTermMemory()
        self.agent_executor = self._build_agent_executor(max_iterations)


    def _build_agent_executor(self, max_iterations: int) -> AgentExecutor:
        """
        ReAct AgentExecutor 를 1회만 생성해 재사용하는 함수
        """
        agent = create_react_agent(
            llm=self.llm.get_chat_model(),
            tools=self.agent_tools,
            prompt=REACT_PROMPT,
        )
        return AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.agent_tools,
            verbose=True,
            max_iterations=max_iterations,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )


    async def run_chat_agent(self, user_input: str):
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
                ("system", CHAT_PROMPTS['chitchat']['confirm']),
                ("user", "{input}")
            ]),
            user_input
        )
        chitchat_output: Any | str = getattr(llm_chitchat_output, "content", str(llm_chitchat_output))

        short_term_history = self.short_term_memory.build_format_history()

        if self.is_chitchat(chitchat_output):
            agent_output = await asyncio.to_thread(
                self.llm.run,
                ChatPromptTemplate.from_messages([
                    ("system", CHAT_PROMPTS['chitchat']['output']),
                    ("user", "{input}")
                ]),
                user_input=user_input,
                history=short_term_history
            )

        else:
            result = await self.agent_executor.ainvoke({"input": user_input})
            tool_result = [
                observation
                for action, observation in result["intermediate_steps"]
            ]

            agent_output = await asyncio.to_thread(
                self.llm.run,
                ChatPromptTemplate.from_messages([
                    ("system", CHAT_PROMPTS['result']['output']),
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

        return agent_output


    def is_chitchat(self, chitchat_output: str) -> bool:
        """
        LLM 이 판단한 일상 대화 여부의 리턴 결과를 통해 True / False 를 지정하는 함수입니다.

        Args:
            chitchat_output (str): LLM 이 판단한 일상 대화 여부 (문자열 True / False)

        Returns:
            bool: True, 그 외 False
        """
        return True if chitchat_output == "True" else False
