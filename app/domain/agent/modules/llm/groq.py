from langchain_groq import ChatGroq

from config.settings import settings
from common.constants.agent.llm_model import LlmModelConstants


class Groq:
    def __init__(self, model_name=LlmModelConstants.MODELS['llama'][0], temperature=0.6):
        self.llm = ChatGroq(
            model_name=model_name,
            temperature=temperature,
            api_key=settings.GROQ_API_KEY,
        )


    def run(self, prompt: str) -> str:
        """
        Groq LLM을 사용하여 입력 텍스트에 대한 응답을 생성하는 함수입니다.

        Args:
            prompt (str): 입력 텍스트

        Returns:
            str: 생성된 응답
        """
        return self.llm.invoke(prompt)