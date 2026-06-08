# 챗봇 에이전트 API

LangChain ReAct 에이전트 기반 대화형 챗봇 API. 사용자 질문을 **일상 대화 / 정보 요청**으로 분류한 뒤, 정보 요청은 **VectorDB 검색** 또는 **웹 검색** 도구를 LLM 이 스스로 선택해 호출하고, 단기 메모리에 대화 컨텍스트를 누적하여 자연스러운 흐름을 유지합니다.

> LLM `llama-3.1-8b-instant` 으로 1차 chitchat 판정을 거친 후, 일상 대화면 친근체 응답·정보 요청이면 ReAct AgentExecutor 가 `use_db_tool`(Qdrant) 또는 `use_web_tool`(SerpAPI) 중 자율 선택해 호출합니다. 도구 응답은 `CHAT_PROMPTS['result']['output']` 컨텍스트로 다시 LLM 에 주입되어 최종 답변이 생성되며, 모든 발화는 `deque(maxlen=10)` 기반 단기 메모리에 누적됩니다.

---

## 목차

1. [핵심 특징](#핵심-특징)
2. [아키텍처](#아키텍처)
3. [기술 스택](#기술-스택)
4. [프로젝트 구조](#프로젝트-구조)
5. [API 명세](#api-명세)
6. [도메인 상세](#도메인-상세)
7. [임베딩 파이프라인 (Celery)](#임베딩-파이프라인-celery)
8. [Celery 워커 정책](#celery-워커-정책)
9. [남은 제한 사항 & 다음 단계](#남은-제한-사항--다음-단계)

---

## 핵심 특징

| 영역 | 내용 |
|---|---|
| **자연어 질의 응답** | LLM `llama-3.1-8b-instant` (temperature 0.6) 로 사용자 질문 분석 및 답변 생성 |
| **Chitchat / RAG 분기** | 1차 LLM 호출로 일상 대화 여부 판정 → 일상 대화면 친근체 응답, 정보 요청이면 ReAct 에이전트로 위임 |
| **ReAct 에이전트** | `langchain.agents.create_react_agent` + `AgentExecutor` 가 description 만 보고 `use_db_tool`(Qdrant) / `use_web_tool`(SerpAPI) 자율 선택 |
| **단기 메모리** | `deque(maxlen=10)` 기반 발화/응답 히스토리를 LLM 컨텍스트로 주입 |
| **백그라운드 임베딩** | Celery + Redis 로 데이터셋 임베딩을 비동기 처리 (`embed_notice_board` 태스크) |

---

## 아키텍처
![Architecture](storage/screenshots/architecture.png)

---

### Chat 요청 처리 흐름 (`POST /api/v1/chat/`)

```
[Client]        [FastAPI]               [LLM]            [Qdrant / Serp]
   │               │                      │                     │
   │ POST /chat/   │                      │                     │
   ├──────────────►│                      │                     │
   │               │ buffer.append(user)  │                     │
   │               │                      │                     │
   │               │ 1) chitchat 판정     │                     │
   │               │ asyncio.to_thread()  ├────────────────────►│
   │               │                      │ "True" / "False"    │
   │               │                      │◄────────────────────┤
   │               │                                            │
   │               │ ┌─ True (일상 대화) ──────────────────┐    │
   │               │ │  chitchat output 프롬프트로         │    │
   │               │ │  history + user → LLM 답변 생성     │    │
   │               │ └─────────────────────────────────────┘    │
   │               │                                            │
   │               │ ┌─ False (정보 요청) ─────────────────┐    │
   │               │ │  AgentExecutor.ainvoke({input})     │    │
   │               │ │  ReAct: tool 선택 → 호출 → 관찰     │    │
   │               │ │  └─ use_db_tool ───► Qdrant 검색    │    │
   │               │ │  └─ use_web_tool ──► SerpAPI 호출   │    │
   │               │ │                                     │    │
   │               │ │  result output 프롬프트로           │    │
   │               │ │  context + history + user → 최종 답 │    │
   │               │ └─────────────────────────────────────┘    │
   │               │                                            │
   │               │ buffer.append(assistant)                   │
   │ { data }      │                                            │
   │◄──────────────┤                                            │
```

---

### ReAct 에이전트 도구 선택 흐름

```
[AgentExecutor.ainvoke(input)]
       │
       │  REACT_PROMPT (hwchase17/react)
       │  + tools description
       │     ├─ use_db_tool: "도매꾹과 관련된 모든 정보 검색에 사용."
       │     └─ use_web_tool: "도매꾹을 제외한 정보 검색에 사용."
       │
       ▼
[LLM 1차 추론]
       │
       │  Thought: 이 질문은 도매꾹과 관련이 ...
       │  Action: use_db_tool / use_web_tool
       │  Action Input: "..."
       │
       ▼
[Tool 실행 — 클로저로 주입된 DBSearch / WebSearch]
       │
       │  DBSearch.search_qdrant(query)
       │   → SentenceTransformer encode
       │   → qdrant.find_points(board_notice, top_k=5)
       │
       │  WebSearch.search_serp(query)
       │   → SerpAPIWrapper(google, hl=ko, gl=kr)
       │   → knowledge_graph + organic_results 상위 3개 파싱
       │
       ▼
[intermediate_steps 에 (action, observation) 누적]
       │
       │  max_iterations=1 → 1회만 도구 호출
       │
       ▼
[result['intermediate_steps'] 의 observation 만 추출 → context]
```

---

### 데이터셋 임베딩 흐름 (Celery 백그라운드)

```
[Celery Worker]              [Storage]                  [Qdrant]
       │                         │                          │
       │ embed_notice_board()    │                          │
       │ ───────────────────────►│                          │
       │  get_board_notices()    │                          │
       │  (storage/embedding/    │                          │
       │   board/notice.py)      │                          │
       │                         │                          │
       │  for each notice:                                  │
       │    RecursiveCharacterTextSplitter                  │
       │      (chunk_size=100, chunk_overlap=10,            │
       │       separators=["\n"])                           │
       │    SentenceTransformer.encode                      │
       │      (all-MiniLM-L6-v2 → 384-dim)                  │
       │                                                    │
       │  PointStruct(                                      │
       │    id=uuid4(),                                     │
       │    vector=[...],                                   │
       │    payload={document_id, category, doc, ...}       │
       │  )                                                 │
       │                                                    │
       │ qdrant.upsert_points(                              │
       │   "board_notice",                                  │
       │   points=[...]                                     │
       │ ) ────────────────────────────────────────────────►│
       │                                                    │
```

---

### 모델 싱글톤 패턴 (`lru_cache`)

```
   app/core/dependencies/common.py
        ┌────────────────────────────────────┐
        │  @lru_cache(maxsize=1)             │
        │  def get_qdrant_client()           │
        │  def get_embedding_model()         │
        │  def get_groq()                    │
        └────────┬───────────────────────────┘
                 │
       ┌─────────┴───────────────────────────┐
       ▼                                     ▼
   [FastAPI 라우터]                    [Celery 워커]
   Depends(get_chat_agent_service)     직접 호출
       │                                     │
       ▼                                     ▼
   서비스 인스턴스 ◄────────────── 같은 모델 인스턴스 공유
   (요청마다 new but 모델은 공유)         (프로세스당 1회 로드)
```

---

## 기술 스택

### Runtime
- **Python** 3.11+
- **FastAPI** 0.135.3
- **Uvicorn[standard]** 0.44.0 (uvloop, httptools, watchfiles)
- **Pydantic** 2.13.0 / **pydantic-settings** 2.13.1
- **python-multipart**

### LLM / 에이전트
- **LangChain** 0.3.27 (core/community/text-splitters)
- **langchain-groq** 0.3.8
- **langsmith** 0.3.45 (보수적 핀 — 0.4+ 부터 `hub.pull` 시 `dangerously_pull_public_prompt` 게이트 추가)
- **Groq SDK** + `llama-3.1-8b-instant` (temperature 0.6)

### 임베딩 / 벡터 검색
- **sentence-transformers** 5.4.1 (`all-MiniLM-L6-v2`, 384차원, Cosine 거리)
- **qdrant-client** 1.17.1 (Qdrant 서버 v1.15.4)
- **huggingface-hub** 0.35.0

### 외부 검색
- **google-search-results** 2.4.2 (SerpAPI, `langchain_community.SerpAPIWrapper`)

### Async Task & Queue
- **Celery** 5.6.3
- **Redis** 7.4.0 (broker + result backend)
- **Flower** 2.0.1 (모니터링 UI, 포트 5555)

### Database
- **SQLAlchemy** 2.0.49 + **pymysql** 1.1.2 + **aiomysql** 0.3.2
- **alembic** 1.18.4 (마이그레이션)

### HTTP / Dev
- **httpx** (비동기 HTTP)
- **pytest** 9.0.3 + **pytest-asyncio** 1.3.0
- **Jupyter Notebook** 7.5.5 + **ipywidgets** 8.1.8
- **uv** (`uv.lock` 기반 재현 가능한 설치)

---

## 프로젝트 구조

```text
fastapi-chatbot/
├── app/
│   ├── api/
│   │   ├── __init__.py                 # /api 루트 + pkgutil 자동 수집
│   │   └── v1/
│   │       ├── __init__.py             # /v1 + 하위 라우터 자동 등록
│   │       └── chat/
│   │           └── router.py           # POST /api/v1/chat/
│   ├── core/
│   │   ├── config.py                   # pydantic-settings 환경 설정, BASE_DIR, STORAGE_PATH
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
│   │   ├── llm/
│   │   │   └── groq.py                 # Groq 래퍼
│   │   ├── memory/
│   │   │   └── short_term.py           # ShortTermMemory (deque(maxlen=10))
│   │   ├── prompt/
│   │   │   └── chat.py                 # CHAT_PROMPTS (chitchat.confirm / chitchat.output / result.output)
│   │   ├── search/
│   │   │   └── serp.py                 # Serp (SerpAPIWrapper 호출 + 응답 파싱 통합)
│   │   └── tools/
│   │       ├── db_search.py            # DBSearch (qdrant + embedding 주입)
│   │       ├── web_search.py           # WebSearch (Serp 주입)
│   │       └── tool.py                 # build_db_search / build_web_search 클로저 팩토리
│   ├── schemas/
│   │   ├── base.py                     # SuccessResponse 제네릭
│   │   └── chat/
│   │       ├── request.py              # ChatAgentRequest
│   │       └── response.py             # ChatAgentResponse (= SuccessResponse[dict])
│   ├── services/
│   │   ├── agent/
│   │   │   └── chat.py                 # ChatAgentService (chitchat 분기 + ReAct executor)
│   │   └── point/
│   │       └── notice_board.py         # NoticeBoardPointService (공지 임베딩 적재)
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
│   └── 01 refactoring.md               # 리팩토링 노트
├── notebooks/                          # Jupyter 탐색 노트북
├── storage/
│   ├── embedding/board/notice.py       # 임베딩 대상 공지 데이터
│   ├── serp/response.json              # SerpAPI 샘플 응답 (개발용)
│   └── screenshots/                    # README 스크린샷
├── tests/
│   └── test_sample.py
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## API 명세

모든 엔드포인트는 `/api/v1` 프리픽스 아래에 있습니다.

### 챗봇 대화

| Method | Path | 설명 |
|---|---|---|
| `POST` | `/api/v1/chat/` | 사용자 질문 → chitchat 판정 → 일상 대화 응답 / ReAct 도구 호출 → 최종 답변 |

**요청** (`application/json`):

```json
{
  "query": "도매꾹 주문 취소는 어떻게 하나요?"
}
```

**응답** (성공 200):

```json
{
  "code": 200,
  "data": "도매꾹에서 주문 취소는 마이페이지 → 주문 내역에서 가능합니다 😊"
}
```

> 도구를 거치지 않은 일상 대화 응답도 동일한 봉투로 반환됩니다.

**에러 응답** (5xx — LLM 호출 실패, SerpAPI 오류 등):

```json
{
  "code": 500,
  "message": "Internal Server Error",
  "errors": [
    { "detail": "..." }
  ]
}
```

---

## 도메인 상세

### 1) Chitchat 판정 (`ChatAgentService.run_chat_agent` 1단계)

사용자 입력을 단기 메모리에 append 한 뒤, **첫 LLM 호출**로 일상 대화 여부를 분류합니다.

- 시스템 프롬프트: `CHAT_PROMPTS['chitchat']['confirm']`
  - 도매꾹 서비스·기능·정책·계정·주문·배송 관련 질문 → `False`
  - 인사·감정 표현·잡담·추천 요청 → `True`
  - 출력은 반드시 Python Boolean 문자열(`True` / `False`)만 허용
- `asyncio.to_thread` 로 동기 LLM 호출을 워커 스레드 위임 → 이벤트 루프 보호
- `is_chitchat(output)` 이 `True` 면 일상 대화 분기로, 그렇지 않으면 ReAct 분기로

### 2) Chitchat 답변 (일상 대화 분기)

- 시스템 프롬프트: `CHAT_PROMPTS['chitchat']['output']`
- 단기 메모리 history + 사용자 입력 → 친근한 한국어 + 이모지 응답 생성

### 3) ReAct 에이전트 (정보 요청 분기)

`AgentExecutor.ainvoke({"input": ...})` 호출:

- `agent` = `create_react_agent(llm, tools, prompt=hub.pull("hwchase17/react"))`
  - **`REACT_PROMPT` 는 모듈 로드 시 1회만 fetch** (네트워크 I/O 회피) — `app/services/agent/chat.py` 상단에 모듈 변수로 캐싱
- `max_iterations=1` — 1회 도구 호출 후 종료
- `handle_parsing_errors=True` — LLM 이 ReAct 포맷 위반해도 graceful 처리
- `return_intermediate_steps=True` — 도구 결과 추출용

도구는 **클로저 팩토리**(`build_db_search` / `build_web_search`)로 주입됩니다:

```python
@tool
def use_db_tool(query: str) -> str:
    """도매꾹과 관련된 모든 정보 검색에 사용."""
    return db_search.search_qdrant(query)
```

description 이 LLM 에게 도구 선택의 단서가 되므로, 도구 추가 시 description 작성이 중요.

### 4) 도구 — DB 검색 (`use_db_tool`)

- `SentenceTransformer` (`all-MiniLM-L6-v2`) 로 query 임베딩 (384차원, Cosine)
- Qdrant `board_notice` 컬렉션에서 **top-k=5** 유사 청크 검색
- 청크 텍스트(`payload["doc"]`)를 `\n` 으로 join 하여 LLM 컨텍스트로 반환
- 결과가 없으면 `"답변을 생성하지 못하였습니다."` 반환

### 5) 도구 — 웹 검색 (`use_web_tool`)

- `SerpAPIWrapper`(engine=`google`, `hl=ko`, `gl=kr`) 로 검색
- 결과 파싱:
  - `knowledge_graph.description` (있으면 우선)
  - `organic_results[:3]` 의 `snippet` 만 추출
- 결과 없으면 `["No results found."]` 반환

> **주의**: 현재 `Serp.run()` 은 실제 API 호출 대신 `storage/serp/response.json` 의 **샘플 응답을 반환**합니다 (`_load_sample_response`). 실제 호출은 주석 처리된 `self._api.results(query)` 라인. 환경 플래그로 분기 필요.

### 6) 결과 합성 (`CHAT_PROMPTS['result']['output']`)

도구 응답(`tool_result`) + 단기 메모리 history + 사용자 입력을 컨텍스트로 한 번 더 LLM 호출하여 부드러운 어조의 최종 답변 생성. 결과는 단기 메모리에 append.

### 7) 단기 메모리 (`ShortTermMemory`)

```python
class ShortTermMemory:
    def __init__(self, max_messages=10):
        self.buffer = deque(maxlen=max_messages)

    def build_format_history(self):
        return "\n".join([f"{item['role']}: {item['content']}" for item in self.buffer])
```

- `deque(maxlen=10)` — 10턴 이상이면 가장 오래된 항목 자동 제거
- `{role, content}` 딕셔너리를 저장하고 LLM 프롬프트에는 `role: content` 라인으로 직렬화

> **제약**: 현재 `ChatAgentService` 가 매 요청마다 새로 생성되어 메모리가 비어 있음. `session_id` 기반 store 패턴 도입 필요 (`docs/01 refactoring.md` #4).

### 8) lifespan 워밍업 (`app/main.py`)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    get_qdrant_client()     # ← lru_cache 첫 호출 (Qdrant client 연결)
    get_embedding_model()   # ← all-MiniLM-L6-v2 모델 메모리 로드
    get_groq()              # ← ChatGroq 인스턴스 초기화
    yield
    get_qdrant_client().close()
```

앱 부팅 시점에 무거운 자원을 모두 적재 → 첫 요청부터 즉시 응답. 종료 시 Qdrant 클라이언트 명시적 close.

---

## 임베딩 파이프라인 (Celery)

`app/worker/tasks/embedding.py` 의 `embed_notice_board` 태스크는 `storage/embedding/board/notice.py` 의 공지 데이터를 분할·임베딩 후 Qdrant 에 저장합니다.

### 처리 흐름

1. **공지 로드**: `get_board_notices()` 로 `storage/embedding/board/notice.py` 의 공지 데이터 로드
2. **전처리**: `preprocess_text()` — 연속 공백/탭 → 단일 공백, 2개 이상 연속 공백문자 → `\n` 치환
3. **텍스트 분할**: `RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10, separators=["\n"])` 로 청크 생성
4. **임베딩**: `SentenceTransformer.encode` 로 청크당 384차원 벡터 생성
5. **PointStruct 생성**:
   ```python
   PointStruct(
       id=str(uuid.uuid4()),
       vector=[...],
       payload={
           "document_id": f"notice_{doc_idx}",
           "category": "notice",
           "doc_idx": doc_idx,
           "paragraph": chunk_idx,
           "doc": chunk,
           "metadata": document.metadata
       }
   )
   ```
6. **Qdrant 저장**: `board_notice` 컬렉션에 `upsert_points`

### 실행 (Flower 또는 CLI)

```bash
# Flower 웹 UI 에서 태스크 호출
# http://localhost:5555

# 또는 CLI
celery -A app.worker.celery_app call app.worker.tasks.embedding.embed_notice_board
```

> **사전 조건**: Qdrant `board_notice` 컬렉션은 다음 설정으로 사전 생성되어야 합니다.
> ```python
> vectors_config={"size": 384, "distance": "Cosine"}
> ```

> **참고**: 현재 ID 는 `uuid.uuid4()` 라 재실행마다 새 row 가 추가됩니다(중복 누적). 멱등성을 원하면 `uuid5(NAMESPACE_URL, document_id + chunk_idx)` 같은 결정적 ID 로 전환 검토.

---

## Celery 워커 정책

`app/worker/celery_app.py` 의 핵심 설정:

```python
celery.conf.update(
    worker_prefetch_multiplier=1,            # 무거운 임베딩은 한 번에 1개만 선점
    task_acks_late=True,                     # 잡 끝난 뒤 ack → 워커 장애 시 재할당
    task_reject_on_worker_lost=True,         # 워커 사망 시 명시적 reject
    task_time_limit=60 * 30,                 # hard 30분
    task_soft_time_limit=60 * 25,            # soft 25분 (cleanup 기회)
    worker_max_tasks_per_child=200,          # 200 잡마다 자식 재시작 (모델 메모리 누수 방어)
    task_track_started=True,                 # PENDING ↔ STARTED 구분
    task_serializer="json",
    result_serializer="json",
    timezone="Asia/Seoul",
)
```

### 정책별 의도

| 정책 | 왜 이렇게 |
|---|---|
| `worker_prefetch_multiplier=1` | 임베딩은 CPU/메모리 bound. 기본 4 는 한 워커가 4개를 선점해 다른 워커가 놀게 됨. 1로 두면 사용 가능한 워커에 골고루 분배 |
| `acks_late` + `reject_on_worker_lost` | 워커가 SIGKILL/OOM 되면 broker 가 같은 잡 재할당. **단, 현재 `uuid4` 기반 ID 라 멱등하지 않음** → 결정적 ID 로 전환 권장 |
| `task_time_limit=30min` | 데이터셋 일괄 임베딩이 오래 걸릴 수 있어 30분 여유. 멈춘 잡이 워커를 영구 점유하는 사고 차단 |
| `task_soft_time_limit=25min` | hard 보다 5분 짧게. soft 초과 시 `SoftTimeLimitExceeded` 예외 → cleanup 가능 |
| `worker_max_tasks_per_child=200` | 임베딩 모델 메모리가 누적되는 것을 200 잡마다 자식 프로세스 재시작으로 방어 |
| `task_track_started=True` | Flower 에서 PENDING(대기) ↔ STARTED(실행중) 구분 가능 |

---

## 남은 제한 사항 & 다음 단계

### 현재 제한 사항

| 항목 | 상태 | 설명 |
|---|---|---|
| **단기 메모리 누적** | ⚠️ | `ChatAgentService` 가 매 요청마다 새로 생성되어 `ShortTermMemory.buffer` 가 비어 있음. 단순 싱글톤은 사용자 섞임 위험 (`docs/01 refactoring.md` #4) |
| **Qdrant 컬렉션 자동 생성** | ❌ | `board_notice` 컬렉션을 사전 생성 필요 (`size=384, distance=Cosine`). lifespan 보강 필요 |
| **SerpAPI 샘플 응답 하드코딩** | ⚠️ | `Serp.run()` 이 실제 API 호출 대신 `storage/serp/response.json` 만 반환. 환경 플래그로 분기 필요 |
| **응답 스키마** | ⚠️ | `ChatAgentResponse = SuccessResponse[dict]` 인데 실제 반환은 LLM 문자열 → 타입 정렬 필요 |
| **임베딩 멱등성 부재** | ⚠️ | `uuid4` 기반이라 재실행 시 같은 청크가 중복 적재. `uuid5(NAMESPACE_URL, ...)` 로 전환 권장 |
| **Config 깊은 dict** | ⚠️ | `EmbeddingModel.MODELS['hugging_face']['sentence_transformer']['All-MiniLM-L6-v2']['name']` 같은 깊은 키 접근. 오타 시 런타임 KeyError, IDE 자동완성 미지원 |
| **테스트 커버리지** | ❌ | `tests/` 에 샘플만 있고 실질 커버리지 없음 |
| **max_iterations=1** | ⚠️ | ReAct 가 도구 호출 1회만 가능. 복잡한 질의(DB + Web 동시)는 처리 불가 |

### 권장 다음 단계

1. **세션 메모리**: `ChatAgentRequest` 에 `session_id` 추가 + `ShortTermMemoryStore`(`session_id → deque`) 도입
2. **응답 스키마 정정**: `ChatAgentResponse` 를 `SuccessResponse[str]` 또는 명시적 dict 스키마로 정렬, `response_model` 과 일치
3. **lifespan 보강**: `client.collection_exists("board_notice")` → 없으면 `create_collection(size=384, distance="Cosine")` 자동 생성
4. **SerpAPI 환경 분기**: `APP_ENV=local` 일 때만 샘플 응답, 그 외 실제 API 호출
5. **임베딩 멱등화**: `uuid5(NAMESPACE_URL, f"{document_id}:{chunk_idx}")` 로 결정적 ID 전환 → `acks_late` 정책과 정합
6. **Config 평탄화**: 깊은 dict 대신 명시적 dataclass 또는 pydantic settings 필드로 분리
7. **테스트**: 라우터·서비스 단위 테스트 (`app.dependency_overrides` 활용, LLM 은 mock)
8. **ReAct 멀티스텝**: `max_iterations` 를 2~3 으로 늘려 도구 조합 질의 지원 (지연 시간 트레이드오프)

---

## 실행 화면

### 챗봇 UI

![챗봇 UI](storage/screenshots/ui.png)

### 웹 검색 (`use_web_tool`)

![웹 검색](storage/screenshots/web_search.png)

### 벡터DB 검색 (`use_db_tool`)

![벡터DB 검색](storage/screenshots/db_search.png)

### 데모

![실행 화면](storage/screenshots/chatbot_v2.gif)

### Swagger UI

- Swagger UI: `http://localhost:9093/docs`
- ReDoc: `http://localhost:9093/redoc`
