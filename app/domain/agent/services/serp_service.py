from config.settings import settings


class SerpService:
    def __init__(self):
        pass


    def parse_serp(self, results: dict):
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
        parsed = []

        if "description" in knowledge_graph:
            parsed.append(knowledge_graph["description"])

        return parsed


    def parse_organic_results(arg, organic_results: list):
        parsed = []

        for organic_result in organic_results[:3]:
            if "snippet" in organic_result:
                parsed.append(organic_result["snippet"])

        return parsed