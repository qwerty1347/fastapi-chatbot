from fastapi import APIRouter

from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

from app.domain.llm.services.service import GroqLLM

from app.domain.ai_agent.services.service import AiAgentService

from langchain.agents import initialize_agent, Tool




router = APIRouter(prefix="/ai-agent", tags=["AI-Agent"])

ai_agent_service = AiAgentService("2026년 연휴를 알려줘")


llm = GroqLLM(api_key="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")


""" # 1. Qdrant 연결
qdrant = QdrantClient(url="http://qdrant:6333")

# 2. 임베딩 모델 로드
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# 3. 컬렉션 생성 (없으면 생성)
COLLECTION_NAME = "ask"

if COLLECTION_NAME not in [c.name for c in qdrant.get_collections().collections]:
    qdrant.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance="Cosine")  # MiniLM-L6 벡터 사이즈
    ) """

# 4. 문서 예시
docs = [
    {"text": "불이 나면 119에 신고하세요.", "category": "긴급"},
    {"text": "Python 설치 방법: Python을 설치하고 환경 변수를 설정합니다.", "category": "개발"},
    {"text": "VSCode 설치 및 설정: VSCode 설치 후 Python 플러그인을 설치합니다.", "category": "개발"},
    {"text": "위급 상황이 발생하면 112에 신고하세요.", "category": "긴급"},
    {"text": "GIT 설치 및 설정: GIT을 설치하고 원격 repository 에서 소스코드를 clone합니다.", "category": "개발"}
]


@router.get('/')
async def index():
    return {"message": "Hello AI-Agent!"}


@router.get('/index')
async def index_documents():
    """
    # * Upsert 방법
    points = []
    for i, doc in enumerate(docs):
        vector = embedding_model.encode(doc["text"]).tolist()
        points.append(
            PointStruct(
                id=i,
                vector=vector,
                payload={"text": doc["text"], "category": doc["category"]}
            )
        )
    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points) """

    # * 기존 컬렉션 삭제 후 새로 생성
    qdrant.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance="Cosine")
    )

    points = []
    for i, doc in enumerate(docs):
        vector = embedding_model.encode(doc["text"]).tolist()
        points.append(
            PointStruct(
                id=i,
                vector=vector,
                payload={"text": doc["text"], "category": doc["category"]}
            )
        )
    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    return {"message": f"{len(points)} documents indexed successfully"}


@router.get('/ask')
async def ask(question: str = "로컬 PC 설정 방법 알려줘"):
    # 1️⃣ 질문 임베딩
    question_vector = embedding_model.encode(question).tolist()

    # 2️⃣ Qdrant 검색 (top-3)
    results = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=question_vector,
        limit=3
    )

    # 3️⃣ 결과 가공
    answers = []
    for point in results:
        answers.append({
            "text": point.payload.get("text"),
            "category": point.payload.get("category"),
            "score": point.score
        })

    return {
        "question": question,
        "answers": answers
    }


@router.get('/predict')
async def predict(question: str = "로컬 PC 설정 방법 알려줘"):
    question = f"""다음 질문에 답변하기 위해 여러 도구를 사용할 수 있습니다.

    사용 가능한 도구:
    1. WebSearch: 최신 정보 등 정확한 정보가 필요할 경우 검색
    2. QdrantDB: 도매꾹 기념일, 일정, 내부 문서 등 정보가 필요한 경우 검색

    규칙:
    1. 어떤 도구가 필요한지 생각하고 도구 이름만 출력 예) WebSearch

    질문: {question}
    """

    # answer = await llm.predict(question)
    answer = "WebSearch"


    # return {"question": question, "answer": answer}
    print({"question": question, "answer": answer})



    """ from langchain.utilities import GoogleSearchAPIWrapper

    search = GoogleSearchAPIWrapper(
        google_api_key="AIzaSyBO_7kkP8nOKTMAk24qtkCBcTc21ad4mdE",
        google_cse_id="95c0d1a4034ba4382",
        k=3
    ) """

    from langchain.utilities import SerpAPIWrapper

    search = SerpAPIWrapper(
        serpapi_api_key="44468cbd29d9ba235220ed5b9e9258d3537c8aa95087ed70d2a4644777b8cb4f",
        params={
            "engine": "google",
            "hl": "ko",
            "gl": "kr"
        }
    )

    # search_results = search.run("2025년 추석은 언제야?")
    search_results = ['추석은 설날과 더불어 대표적인 한국의 명절로, 음력 8월 15일이다. 한가위라고도 불린다. 가을 저녁에 보름달 보며 소원을 비는 민족의 대명절이다. 한가위는 농경사회인 한국의 명절로 가배일, 추수 전 덜 익은 쌀로 빚은 송편과 햇과일을 진설하고 조상들께 감사의 마음으로 차례를 지냈다.', '추석 type: 명절.', '추석 kgmid: /m/03rb1r.', '추석 날짜: 2025년 10월 6일 월요일.', '2025년 추석 연휴는 10월3일(금) 개천절부터 9일(목) 한글날까지 7일간 이어진다. 특히 연휴 다음날인 10월10일이 금요일이어서, 하루 휴가를 활용 ...', "추석 연휴는 · 10월3일 개천절부터 9일 한글날까지 · 7일간 이어지는 '황금연휴' · \u200b · 연휴 다음날인 · 10월10일 금요일에 휴가를 내면 · 3일부터 12일까지 ...", '10월 3일 (금)을 시작으로 추석 연휴가 이어집니다. 추석에 일요일이 포함되어 8일이 대체 휴일로 지정되었습니다. 여기에 개천절까지 더해져 기본적으로 ...', '정월대보름(음 1월 15일)은 2월 12일, 단오(음 5월 5일)는 5월 31일, 칠석(음 7월 7일)은 8월 29일, 추석(음 8월 15일)은 10월 6일이다. 한식은 4월 5일, ...', "2025년 추석연휴는 3일 개천절부터 9일 한글날까지 죽 이어지면서 '7일의 황금연휴'가 된다. 우주항공청은 2025년도 우리나라 달력 제작의 기준이 ...", '추석 연휴 시작일: 10월 5일 일요일이므로, 10월 8일 수요일이 대체공휴일로 지정되었습니다.', '2025년 공휴일 정리표 ; 14, 10월 05일(일), 추석 연휴 ; 15, 10월 06일(월), 추석 ; 16, 10월 07일(화), 추석 연휴 ; 17, 10월 08일(수), 대체공휴일(추석).', "'열흘간의 황금연휴' 여행 떠나 볼까\u200b 2025년 10월 추석연휴가 가능성이 크다. 3일 개천절이 금요일이고, 6일 추석, 7일 추석 다음날, 9일  한글날이다. 이 ...", '2025 공휴일 ; 설날 연휴, 1월 28일(화) ~ 30일(목) · 개천절 ; 삼일절 대체공휴일, 3월 3일 (월요일), 추석 연휴 ; 어린이날, 5월 5일(월), 한글날 ; 부처님 ...']

    # print(search_results)

    search_results = " ".join(search_results)

    question = f"""너는 전문적인 상담사입니다. 상담에 맞는 단어가 포함된 답변으로만 출력하세요.

    규칙:
    1. 질문과 정보들을 분석
    2. 간단한 문장으로 요약하고 분석에 적절하지 않은 답변은 제외

    질문: 2025년 추석은 언제야?

    정보: {search_results}
    """

    # answer = await llm.predict(question)
    answer = "2025년 추석은 10월 6일 월요일입니다. 추석 연휴는 10월 3일 개천절부터 9일 한글날까지 7일간 이어집니다. 일반적으로 추석 연휴는 7일째 되는 날인 10월 10일 금요일입니다."


    print(answer)





    # return {
    #     "question": question,
    #     "answer": answer,
    #     "search_results": search_results
    # }

    return f"LLM 분석: {answer}\n검색 결과: {search_results}"




    tools = [
        Tool(name="WebSearch", func=ai_agent_service.web_search_function, description="최신 정보 검색"),
        Tool(name="QdrantDB", func=ai_agent_service.qdrant_search_function, description="내부 문서 검색")
    ]

    agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)



    # result = agent.run("파이썬에서 웹 크롤링하는 방법 알려줘")
    # print(result)
    return {"result": "succ"}

    pass



@router.get('/test')
async def test():
    await ai_agent_service.handle_ai_agent()
    return {"result": "succ"}
