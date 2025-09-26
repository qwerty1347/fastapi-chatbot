from app.domain.ai_agent.modules.groq import GroqModule
from app.domain.ai_agent.modules.serp import SerpModule
from common.constants.llm_model import LlmModelConstants
from config.settings import settings
import asyncio



class AiAgentService:
    def __init__(self, user_prompt: str):
        self.user_prompt = user_prompt


    async def handle_ai_agent(self):
        # tool = await self.select_tool()
        # print("tool: " + tool)


        # Tool.from_function(
        #     name="QdrantDB",
        #     func=self.qdrant_search_function,
        #     description="""
        #     내부 문서 검색용 도구입니다.
        #     규칙: 질문에 답변하려면 QdrantDB를 사용하세요.
        #     출력: 도구 이름만 QdrantDB
        #     """,
        #     coroutine=self.qdrant_search_function
        # )


        from langchain.agents import initialize_agent, Tool, AgentType
        tools = [
            Tool.from_function(
                name="WebSearch",
                func=self.web_search_function,
                description="""
                최신 정보 검색용 도구입니다.
                규칙: 질문에 답변하려면 WebSearch를 사용하세요.
                출력: 도구 이름만 WebSearch
                """,
                coroutine=self.web_search_function
            ),
        ]


        llm = GroqModule(
            groq_api_key=settings.GROQ_API_KEY,
            model=LlmModelConstants.MODELS['llama'][0]
        )

        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            agent_kwargs={"system_message": "2025년 연휴를 알려줘"},
        )

        print("agent: " + str(agent))
        return agent



        # ! 3-1번
        # search_result = await self.request_search()
        search_result = ['2026년 공휴일 정리표 ; 1, 01월 01일(목), 신정(양력설) ; 2, 02월 16일(월), 설날 연휴 ; 3, 02월 17일(화), 설날 ; 4, 02월 18일(수), 설날 연휴.', '줄어든 내용을 자세히 살펴보면, 2025년에는 설날과 연계하여 임시공휴일이 하루 있었고, 벚꽃대선, 현충일이 주말이 아니었는데요. 2026년에는 아직 임시 ...', '2026년의 경우, 삼일절(3월 1일)과 부처님오신날(5월 24일)이 일요일과 겹치면서 대체공휴일이 적용되었으나, 겹치는 일수만큼 총 공휴일 수는 줄어들었다 ...', '2. 2026 황금연휴 | 대체공휴일 포함 황금연휴 모음 ; 3월 1일-3월 2일, 삼일절 + 대체공휴일, 월요일 하루만 쉬는 짧은 연휴 ; 5월 3일-5월 5일, 어린이날 ...', '2026년 2월 14일~18일(토·일요일 및 설날 연휴, 5일), 2월 28일~3월 2일(토요일, 3·1절 및 3·1절 대체공휴일, 3일), 5월 23일~25일(토요일, 부처님오신날 ...', '이 중 현충일(6월 6일), 광복절(8월 15일), 추석 연휴 마지막 날(9월 26일), 개천절(10월 3일)은 토요일과 겹쳐 실제 쉴 수 있는 휴일 수에는 포함되지 ...', '2026년 2월 · 공휴일: 2월 16일 (월) ~ 18일 (수): 설날 연휴 · 주요 이벤트: 발렌타인데이(2/14) · 학교 일정: 졸업식 · 손 없는 날: 2/6(금), 2 ...', '2026년 공휴일은 총 70일로 올해보다 2일 늘어난다. 주 5일제 근무자의 경우 내년 휴일 수는 올해보다 하루 적은 118일이다. 우주항공청은 우리나라 달력 ...', '따라서 삼일절, 부처님오신날, 광복절, 개천절, 한글날, 성탄절이 3일 연휴고 설날은 2월 17일이라 토요일~수요일 연휴이며 2021년 이후 5년 만에 발렌타인 데이를 설 연휴 ...', '2026년 가장 긴 연휴는 설날(2월 17일) 전후로 닷새를 쉬는 2월 14~18일이다. 주말 이틀과 설 연휴 사흘이 연달아 있다. 주말 또는 대체공휴일로 이어지는 ...']
        # print(search_result)


        pass





    async def request_search(self):
        serp = SerpModule()
        return await serp.request_search(self.user_prompt)



    # Tool async 함수
    async def web_search_function(self, query: str) -> str:
        await asyncio.sleep(0.1)  # 예시용
        return f"[WebSearch 결과] {query}"

    async def qdrant_search_function(self, query: str) -> str:
        await asyncio.sleep(0.1)  # 예시용
        return f"[QdrantDB 결과] {query}"