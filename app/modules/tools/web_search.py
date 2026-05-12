from app.modules.search.serp import Serp


class WebSearch:
    def __init__(self, serp: Serp):
        self.serp = serp


    def search_serp(self, query: str) -> str:
        """
        Serp API를 사용하여 입력 텍스트에 대한 웹 검색 결과를 가져오고 파싱하여 리턴하는 함수입니다.

        Args:
            query (str): 검색할 텍스트 쿼리

        Returns:
            str: 웹 검색 결과를 하나의 문자열로 합쳐 반환
        """
        response = self.serp.run(query)
        parsed = self.serp.parse(response)

        return "\n".join(parsed)
