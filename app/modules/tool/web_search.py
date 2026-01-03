from app.modules.search.serp import Serp
from app.services.serp_service import SerpService


class WebSearch:
    def __init__(self):
        self.serp = Serp()


    def search_serp(self, query: str) -> str:
        """
        Serp API를 사용하여 입력 텍스트에 대한 웹 검색 결과를 가져오고 파싱하여 리턴하는 함수입니다.

        Args:
            query (str): 검색할 텍스트 쿼리

        Returns:
            str: 웹 검색 결과를 하나의 문자열로 합쳐 반환
        """
        serp_service = SerpService()
        response = self.serp.run(query)
        parsed = serp_service.parse_serp(response)

        return "\n".join(parsed)