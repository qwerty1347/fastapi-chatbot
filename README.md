# 챗봇 에이전트 API

LangChain ReAct 에이전트 기반 대화형 챗봇 API. 사용자의 질문을 **일상 대화/정보 요청** 으로 분류한 뒤, 정보 요청은 **VectorDB 검색** 또는 **웹 검색** 도구를 LLM 이 스스로 선택해 호출하고, 단기 메모리에 대화 컨텍스트를 누적하여 자연스러운 흐름을 유지합니다.

## 🚀 주요 기능

- **자연어 질의 응답**: Groq 의 Llama 3.1-8B-Instant 모델로 사용자의 질문을 분석하고 답변 생성
- **Chitchat / RAG 분기**: 1차 LLM 호출로 일상 대화 여부를 판단해, 일상 대화면 바로 응답·정보 요청이면 ReAct 에이전트로 전달
- **ReAct 에이전트**: `langchain.agents.create_react_agent` 기반. 다음 두 Tool 을 LLM 이 자율 선택
  - `use_db_tool`: Qdrant `board_notice` 컬렉션에서 임베딩 유사도 검색
  - `use_web_tool`: SerpAPI(Google) 결과를 파싱해 상위 3개 스니펫 반환
- **단기 메모리**: `deque(maxlen=10)` 기반 발화/응답 히스토리를 LLM 컨텍스트로 주입
- **백그라운드 임베딩**: Celery + Redis 로 임베딩을 비동기 처리

## 🛠️ 기술 스택

| 영역 | 사용 기술 |
|---|---|
| Web | FastAPI 0.135.3, Uvicorn 0.44.0 (standard), python-multipart |
| 검증/설정 | Pydantic 2.13.0, pydantic-settings 2.13.1 |
| LLM / Agent | LangChain 0.3.27 (core/community/text-splitters), langchain-groq 0.3.8, langsmith 0.3.45 |
| LLM 모델 | Groq `llama-3.1-8b-instant` (temperature 0.6) |
| 임베딩 | sentence-transformers 5.4.1 (`all-MiniLM-L6-v2`, 384차원, Cosine) |
| 벡터 DB | qdrant-client 1.17.1 (Qdrant 서버 v1.15.4) |
| 작업 큐 | Celery 5.6.3, Redis 7.4.0, Flower 2.0.1 |
| HTTP | httpx |
| 테스트 | pytest 9.0.3, pytest-asyncio 1.3.0 |
| 런타임 | Python 3.11+ |

## 📦 프로젝트 구조

```text
fastapi-chatbot/
├── app/
│   ├── api/
│   │   ├── __init__.py                 # pkgutil 기반 버전(v1) 자동 수집
│   │   └── v1/
│   │       ├── __init__.py             # pkgutil 기반 라우터 자동 수집
│   │       └── chat/
│   │           └── router.py           # POST /api/v1/chat
│   ├── core/
│   │   ├── config.py                   # pydantic-settings 환경 설정
│   │   ├── logging.py                  # 로깅 초기화
│   │   ├── dependencies/
│   │   │   ├── common.py               # get_qdrant_client / get_embedding_model / get_groq (lru_cache) + get_qdrant
│   │   │   └── chat.py                 # Serp / DBSearch / WebSearch / ChatAgentService 팩토리
│   │   ├── exceptions/
│   │   │   ├── custom.py               # BusinessException
│   │   │   └── handler.py              # 글로벌 예외 핸들러 등록
│   │   └── utils/
│   │       └── response.py             # success_response / error_response 헬퍼
│   ├── infrastructure/
│   │   ├── storage/board.py            # 게시판 공지 로더
│   │   └── vectordb/qdrant.py          # Qdrant 클라이언트 래퍼 (client 주입형)
│   ├── modules/
│   │   ├── llm/groq.py                 # ChatGroq 래퍼 (get_chat_model getter)
│   │   ├── memory/short_term.py        # ShortTermMemory (deque 기반)
│   │   ├── prompt/chat.py              # CHAT_PROMPTS (chitchat/result)
│   │   ├── search/serp.py              # SerpAPIWrapper 호출 + 응답 파싱 통합
│   │   └── tools/
│   │       ├── db_search.py            # DBSearch (qdrant + embedding 주입)
│   │       ├── web_search.py           # WebSearch (Serp 주입)
│   │       └── tool.py                 # build_db_search / build_web_search 클로저 팩토리
│   ├── schemas/
│   │   └── chat/request.py             # ChatAgentRequest
│   ├── services/
│   │   ├── agent/chat.py               # ChatAgentService (chitchat 분기 + ReAct executor)
│   │   └── point/notice_board.py       # NoticeBoardPointService (공지 임베딩 적재)
│   ├── worker/
│   │   ├── celery_app.py               # Celery 앱 (queue: embedding)
│   │   └── tasks/
│   │       ├── embedding.py            # embed_notice_board (lru_cache 캐시 함수 직접 호출)
│   │       └── test.py                 # 샘플 add 태스크
│   └── main.py                         # FastAPI 진입점 (lifespan 워밍업, CORS, 예외 등록)
├── config/
│   ├── embedding_model.py              # 임베딩 모델 메타 (all-MiniLM-L6-v2)
│   └── llm_model.py                    # LLM 모델 메타 (llama-3.1-8b-instant)
├── docs/
│   └── 01 refactoring.md
├── notebooks/
├── storage/
│   ├── embedding/board/notice.py       # 임베딩 대상 공지 데이터
│   ├── serp/response.json              # SerpAPI 샘플 응답 (개발용)
│   └── screenshots/                    # README 스크린샷
├── tests/
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
└── README.md
```

## 🐳 실행 (Docker Compose)

```bash
docker compose up -d qdrant redis
docker compose up -d app celery flower
```

| 서비스 | 포트 | 용도 |
|---|---|---|
| app (FastAPI) | `9098 → 8000` | API |
| Jupyter (app 컨테이너) | `8888` | 노트북 실험 환경 |
| Qdrant | `6333` (HTTP), `6334` (gRPC) | 벡터 DB |
| Redis | `6379` | Celery 브로커/백엔드 |
| Flower | `5555` | Celery 모니터링 |

## 📡 API

### `POST /api/v1/chat/`

사용자의 자연어 질문을 받아 chitchat / 정보검색을 자동 분기 후 답변을 반환합니다.

- **요청**: `application/json`

```json
{ "query": "안녕?" }
```

- **응답** (현재 라우터 구현, `app/api/v1/chat/router.py`)

```json
{
    "code": "200",
    "data": "안녕! 😊 좋은 하루 보내고 있어? 오늘 무슨 일있어?"
}
```

## 🧠 에이전트 처리 흐름

1. 사용자 입력을 `ShortTermMemory.buffer` 에 append
2. **Chitchat 분류**: `CHAT_PROMPTS['chitchat']['confirm']` 프롬프트로 LLM 호출 → `"True"`/`"False"`
3. 분기
   - **True (일상 대화)**: `CHAT_PROMPTS['chitchat']['output']` 으로 친근체 응답 생성
   - **False (정보 요청)**: 캐시된 `AgentExecutor` 가 `use_db_tool` / `use_web_tool` 중 선택해 호출 → 결과를 `CHAT_PROMPTS['result']['output']` 컨텍스트로 주입해 최종 답변 생성
4. 답변을 `ShortTermMemory.buffer` 에 append (다음 턴 history 로 사용)

## 🧪 임베딩 파이프라인 (Celery)

`app/worker/tasks/embedding.py` 의 `embed_notice_board` 태스크는 `storage/embedding/board/notice.py` 의 공지 데이터를 `RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)` 로 분할한 뒤 `all-MiniLM-L6-v2` 로 임베딩하여 Qdrant `board_notice` 컬렉션에 `upsert` 합니다 (`app/services/point/notice_board.py`).

> Qdrant 컬렉션은 사전에 `vectors_config={"size": 384, "distance": "Cosine"}` 로 생성되어 있어야 합니다.

## ⚠️ 남은 제한 사항

- **단기 메모리 누적**: `ChatAgentService` 가 매 요청마다 생성되어 `ShortTermMemory.buffer` 가 비어 있음. 단순 싱글톤은 사용자 섞임 위험이 있으므로 `session_id` 키 기반 Store 패턴으로 전환 필요 (`docs/01 refactoring.md` #4).
- **Qdrant 컬렉션 자동 생성**: `board_notice` 컬렉션을 사전에 `size=384, distance=Cosine` 으로 생성해두어야 함. lifespan 에서 `create_collection` 호출 보강 권장.
- **SerpAPI 샘플 응답 하드코딩**: `Serp.run()` 이 실제 API 호출 대신 `storage/serp/response.json` 만 반환 (`Serp._load_sample_response`). 환경 플래그로 분기 필요 (`docs/01 refactoring.md` #11).
- **Config 깊은 dict**: `EmbeddingModel.MODELS['hugging_face']['sentence_transformer']['All-MiniLM-L6-v2']['name']` 형태의 깊은 키 접근. 오타 시 런타임 KeyError, IDE 자동완성 미지원 (`docs/01 refactoring.md` #12).

### 권장 다음 단계

1. `handle_agent` 가 `str` 반환 + 라우터가 `success_response` 로 감싸 응답 (#7)
2. `ChatAgentRequest` 에 `session_id` 추가 + `ShortTermMemoryStore` (`session_id -> deque`) 도입 (#4)
3. `ChatAgentResponse` 스키마 정의 후 `response_model` 지정 (#8)
4. lifespan 에 `collection_exists` 확인 + `create_collection` 보강

## 📸 실행 화면

![챗봇 UI](storage/screenshots/ui.png)
![웹 검색](storage/screenshots/web_search.png)
![벡터DB 검색](storage/screenshots/db_search.png)
![실행 화면](storage/screenshots/chatbot_v2.gif)