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
        # results = self.serp.results(query)
        results = self.serp_service.load_sample_response()

        return self.serp_service.parse_serp(results)