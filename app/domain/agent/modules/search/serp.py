from langchain.utilities import SerpAPIWrapper

from config.settings import settings


class Serp:
    def __init__(self):
        self.client =  SerpAPIWrapper(
            serpapi_api_key=settings.SERP_API_KEY,
            params={
                "engine": "google",
                "hl": "ko",
                "gl": "kr"
            }
        )


    async def request_search(self, query: str):
        return self.client.run(query)