import asyncio
from groq import Groq

class GroqLLM:
    def __init__(self, api_key: str = None):
        # API 키 없으면 환경변수에서 가져오기
        self.client = Groq(api_key=api_key)

    async def predict(self, prompt: str, model: str = "llama-3.1-8b-instant") -> str:
        """
        Groq LLaMA 3 모델로 프롬프트를 보내고 응답 반환 (비동기 처리)
        """
        # 동기 SDK 호출을 비동기처럼 실행
        def sync_call():
            completion = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return completion.choices[0].message.content

        return await asyncio.to_thread(sync_call)
