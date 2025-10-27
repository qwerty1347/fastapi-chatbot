class SerpService:
    def __init__(self):
        pass


    def parse_serp(self, results: dict):
        """
        Serp API의 결과를 파싱하여 리스트 형태로 리턴하는 함수입니다.

        Args:
            results (dict): Serp API의 결과

        Returns:
            list: 파싱된 결과
        """
        parsed = []
        knowledge_graph = results.get('knowledge_graph')
        organic_results = results.get('organic_results')

        if knowledge_graph is not None:
            parsed.extend(self.parse_knowledge_graph(knowledge_graph))

        if organic_results is not None:
            parsed.extend(self.parse_organic_results(organic_results))

        if not parsed:
            parsed.append("No results found.")

        return parsed


    def parse_knowledge_graph(self, knowledge_graph: dict):
        """
        Serp API의 knowledge_graph 결과를 파싱하여 리스트 형태로 리턴하는 함수입니다.

        Args:
            knowledge_graph (dict): Serp API의 knowledge_graph 그래프 결과

        Returns:
            list: 파싱된 결과
        """
        parsed = []

        if "description" in knowledge_graph:
            parsed.append(knowledge_graph["description"])

        return parsed


    def parse_organic_results(arg, organic_results: list):
        """
        Serp API의 organic_results 결과를 파싱하여 리스트 형태로 리턴하는 함수입니다.

        Args:
            organic_results (list): Serp API의 organic_results 검색 결과

        Returns:
            list: 파싱된 결과
        """
        parsed = []

        for organic_result in organic_results[:3]:
            if "snippet" in organic_result:
                parsed.append(organic_result["snippet"])

        return parsed