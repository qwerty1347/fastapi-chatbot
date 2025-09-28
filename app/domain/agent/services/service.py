from langchain.agents import initialize_agent, Tool, AgentType

from app.domain.agent.modules.llm.groq import Groq


class AgentService:
    def __init__(self):
        self.llm_wrapper = Groq()

        self.observations = []

        self.tools = [
            Tool.from_function(
                name="WebSearch",
                func=self.web_search,
                description="최신 정보 등 정확한 정보가 필요할 경우 검색용"
            ),
            Tool.from_function(
                name="QdrantSearch",
                func=self.qdrant_search,
                description="회사(도매꾹) 정보, 내부 문서 등 정보가 필요한 경우 검색용"
            )
        ]


        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm_wrapper.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            max_iterations=1,
            early_stopping_method="generate",
        )


    def web_search(self, query: str) -> str:

        results = [
            '추석은 설날과 더불어 대표적인 한국의 명절...',
            '2025년 추석은 10월 6일 월요일입니다.',
            '2025년 추석 연휴는 10월 3일부터 10월 9일까지입니다.'
        ]


        obs = " ".join(results)
        self.observations.append(obs)
        return obs


    def qdrant_search(self, query: str) -> str:
        obs = f"Qdrant 검색 결과: {query} 관련 데이터."
        self.observations.append(obs)
        return obs




    def handle_ai_agent(self, query: str) -> dict:
        question = "2025년 추석에 대해 알려줘"

        self.agent.run(question)

        summary = self.llm_wrapper.run_llm(
            f"""당신은 전문적인 상담사입니다. 상담에 맞는 단어가 포함된 답변으로만 출력하세요.

            규칙:
            1. 질문과 정보들을 분석
            2. 간단한 문장으로 요약하고 분석에 적절하지 않은 답변은 제외

            질문: 2025년 추석에 대해 알려줘

            정보: {''.join(self.observations)}"""
        )

        return {
            "final_answer": summary,
            "observations": self.observations
        }