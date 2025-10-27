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
        """
        Serp API를 사용하여 입력 텍스트에 대한 결과를 리턴하는 함수입니다.

        Args:
            query (str): 입력 텍스트

        Returns:
            dict: 결과
        """
        # return self.serp.results(query)
        return self.load_sample_response()


    def load_sample_response(self):
        """
        Serp API의 샘플 response.json 파일을 읽어 결과를 리턴하는 함수입니다.

        Returns:
            dict: 결과
        """
        file_path = settings.STORAGE_PATH + "/serp/response.json"
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)