from app.core.config import config
from config.llm_model import LLMModel

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq


class Groq:
    def __init__(self):
        self.llm = ChatGroq(
            model_name=LLMModel.MODELS['llama']['3.1-8b-instant']['model'],
            temperature=LLMModel.MODELS['llama']['3.1-8b-instant']['temperature'],
            api_key=config.GROQ_API_KEY,
        )


    def run(self, prompt: ChatPromptTemplate, user_input: str, context: str | None = None, history: str | None = None) -> str:
        """
        Groq LLM을 사용하여 입력 텍스트에 대한 응답을 생성하는 함수입니다.

        Args:
            prompt (ChatPromptTemplate): LLM 에 전달할 프롬프트 템플릿
            user_input (str): 사용자 입력 텍스트


        Returns:
            str: LLM 이 생성한 응답 텍스트
        """
        inputs = {"input": user_input}

        if context is not None:
            inputs['context'] = context

        if history is not None:
            inputs['history'] = history

        chain = prompt | self.llm

        return chain.invoke(inputs)
