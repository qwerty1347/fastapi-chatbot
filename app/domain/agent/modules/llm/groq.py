from langchain_groq import ChatGroq

from config.settings import settings
from common.constants.llm_model import LlmModelConstants


class Groq:
    def __init__(self, model_name=LlmModelConstants.MODELS['llama'][0], temperature=0.6):
        self.llm = ChatGroq(
            model_name=model_name,
            temperature=temperature,
            api_key=settings.GROQ_API_KEY,
        )


    def run_llm(self, prompt: str) -> str:
        return self.llm.predict(prompt)