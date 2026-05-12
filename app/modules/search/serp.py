import json

from langchain_community.utilities import SerpAPIWrapper

from app.core.config import config


class Serp:
    def __init__(self):
        self._api = SerpAPIWrapper(
            serpapi_api_key=config.SERP_API_KEY,
            params={
                "engine": "google",
                "hl": "ko",
                "gl": "kr",
            },
        )


    def run(self, query: str) -> dict:
        """
        Serp API를 사용하여 입력 텍스트에 대한 결과를 리턴하는 함수입니다.

        Args:
            query (str): 입력 텍스트

        Returns:
            dict: Serp API 응답
        """
        # return self._api.results(query)
        return self._load_sample_response()


    def parse(self, results: dict) -> list[str]:
        """
        Serp API의 결과를 파싱하여 문자열 리스트로 리턴하는 함수입니다.

        Args:
            results (dict): Serp API의 결과

        Returns:
            list[str]: 파싱된 결과
        """
        parsed: list[str] = []
        knowledge_graph = results.get("knowledge_graph")
        organic_results = results.get("organic_results")

        if knowledge_graph is not None:
            parsed.extend(self._parse_knowledge_graph(knowledge_graph))

        if organic_results is not None:
            parsed.extend(self._parse_organic_results(organic_results))

        if not parsed:
            parsed.append("No results found.")

        return parsed


    def _load_sample_response(self) -> dict:
        """
        Serp API의 샘플 response.json 파일을 읽어 결과를 리턴하는 함수입니다.

        Returns:
            dict: 샘플 응답
        """
        file_path = config.STORAGE_PATH + "/serp/response.json"
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)


    def _parse_knowledge_graph(self, knowledge_graph: dict) -> list[str]:
        """
        Serp API의 knowledge_graph 결과를 파싱하여 리스트 형태로 리턴하는 함수입니다.

        Args:
            knowledge_graph (dict): Serp API의 knowledge_graph 결과

        Returns:
            list[str]: 파싱된 결과
        """
        if "description" in knowledge_graph:
            return [knowledge_graph["description"]]
        return []


    def _parse_organic_results(self, organic_results: list) -> list[str]:
        """
        Serp API의 organic_results 결과를 파싱하여 리스트 형태로 리턴하는 함수입니다.

        Args:
            organic_results (list): Serp API의 organic_results 검색 결과

        Returns:
            list[str]: 파싱된 결과
        """
        return [
            organic_result["snippet"]
            for organic_result in organic_results[:3]
            if "snippet" in organic_result
        ]
