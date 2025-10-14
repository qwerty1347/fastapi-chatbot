import json

from langchain_community.utilities import SerpAPIWrapper

from app.domain.agent.services.serp_service import SerpService
from config.settings import settings


class Serp:
    def __init__(self):
        self.serp_service = SerpService()
        self.serp = SerpAPIWrapper(
            serpapi_api_key=settings.SERP_API_KEY,
            params={
                "engine": "google",
                "hl": "ko",
                "gl": "kr"
            }
        )


    def run(self, query: str):
        # return self.serp.results(query)
        return self.load_sample_response()


    def load_sample_response(self):
        file_path = settings.STORAGE_PATH + "/serp/response.json"
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)