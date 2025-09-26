from app.domain.ai_agent.modules.groq import GroqModule
from common.constants.llm_model import LlmModelConstants
from config.settings import settings


class LlmService:
    def __init__():
        pass


    async def do_llm(self, prompt):
        groq = GroqModule()

        print("do_llm: " + await groq.request_llm())

        return await groq.request_llm(prompt=prompt)


    async def select_tool(self, user_prompt):
        prompt: str = f"""
            다음 질문에 답변하기 위해 여러 도구를 사용할 수 있습니다.

            사용 가능한 도구:
            1. WebSearch: 최신 정보 등 정확한 정보가 필요할 경우 검색
            2. QdrantDB: 도매꾹 기념일, 일정, 내부 문서 등 정보가 필요한 경우 검색

            규칙:
            1. 어떤 도구가 필요한지 생각하고 도구 이름만 출력 예) WebSearch

            질문: {user_prompt}
            """

        return await self.do_llm(prompt=prompt)