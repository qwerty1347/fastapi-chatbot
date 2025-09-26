import asyncio

from langchain.llms.base import LLM
from groq import Groq
from typing import List, Optional

from common.constants.llm_model import LlmModelConstants
from config.settings import settings


class GroqModule(LLM):
    def __init__(self, groq_api_key=settings.GROQ_API_KEY, model=LlmModelConstants.MODELS['llama'][0]):
        self.client = Groq(api_key=groq_api_key)
        self.model = model

    @property
    def _llm_type(self) -> str:
        return "groq"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        return self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        ).choices[0].message.content

    async def _acall(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        return await asyncio.to_thread(
            lambda: self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            ).choices[0].message.content
        )




    """ def sync_call(self, prompt):
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )

        return completion.choices[0].message.content """


    """ async def request_llm(self, prompt):
        return await asyncio.to_thread(self._call(prompt))
    """