# 챗봇 에이전트 API

LangChain ReAct 에이전트 기반 대화형 챗봇 API. 사용자 질문을 **일상 대화 / 정보 요청**으로 분류한 뒤, 정보 요청은 **VectorDB 검색** 또는 **웹 검색** 도구를 LLM이 스스로 선택해 호출하고, 단기 메모리에 대화 컨텍스트를 누적하여 자연스러운 흐름을 유지합니다.

> Groq `llama-3.1-8b-instant` 으로 1차 chitchat 판정을 거친 후, 일상 대화면 친근체 응답·정보 요청이면 ReAct AgentExecutor 가 `use_db_tool`(Qdrant) 또는 `use_web_tool`(SerpAPI) 중 자율 선택해 호출합니다. 도구 응답은 `CHAT_PROMPTS['result']['output']` 컨텍스트로 다시 LLM에 주입되어 최종 답변이 생성되며, 모든 발화는 `deque(maxlen=10)` 기반 단기 메모리에 누적됩니다.

---

## 목차

1. [핵심 특징](#핵심-특징)
2. [아키텍처](#아키텍처)
3. [기술 스택](#기술-스택)
4. [프로젝트 구조](#프로젝트-구조)
5. [도메인 상세](#도메인-상세)
6. [임베딩 파이프라인 (Celery)](#임베딩-파이프라인-celery)
7. [남은 제한 사항 & 다음 단계](#남은-제한-사항--다음-단계)

---

## 핵심 특징

| 영역 | 내용 |
|---|---|
| **자연어 질의 응답** | Groq `llama-3.1-8b-instant` (temperature 0.6) 모델로 사용자 질문 분석 및 답변 생성 |
| **Chitchat / RAG 분기** | 1차 LLM 호출(`CHAT_PROMPTS['chitchat']['confirm']`)로 일상 대화 여부 판정 → 일상 대화면 친근체 응답, 정보 요청이면 ReAct 에이전트로 위임 |
| **ReAct 에이전트** | `langchain.agents.create_react_agent` + `AgentExecutor`(max_iterations=1, `handle_parsing_errors=True`). 클로저 팩토리(`build_db_search` / `build_web_search`)로 도구를 주입 |
| **두 가지 도구** | `use_db_tool` (Qdrant `board_notice` 유사도 검색) / `use_web_tool` (SerpAPI 결과 상위 3개 스니펫) — LLM 이 description 보고 자율 선택 |
| **단기 메모리** | `deque(maxlen=10)` 기반 발화/응답 히스토리를 LLM 컨텍스트로 주입 (`ShortTermMemory.build_format_history`) |
| **백그라운드 임베딩** | Celery + Redis 로 데이터셋 임베딩을 비동기 처리 (`embed_notice_board` 태스크) |
| **의존성 주입 / 모델 싱글톤** | `lru_cache`로 Qdrant·SentenceTransformer·ChatGroq를 프로세스당 1회만 로드. FastAPI는 `Depends`로, Celery 워커는 동일 캐시 함수 직접 호출 |
| **lifespan 워밍업** | 앱 부팅 시 Qdrant 클라이언트·임베딩 모델·LLM 미리 로드 → 첫 요청 지연 제거, 종료 시 graceful close |
| **이벤트 루프 보호** | `Groq.run` 등 동기 LLM 호출을 `asyncio.to_thread()`로 워커 스레드에 위임 |
| **버전 라우팅** | `app/api/`에서 라우터를 `pkgutil`로 자동 수집해 `/api/v1/...`로 등록 |

---

## 아키텍처

### Chat 요청 처리 흐름

```
[Client]        [FastAPI]            [Groq]            [Qdrant / Serp]
   │               │                    │                     │
   │ POST /chat/   │                    │                     │
   ├──────────────►│                    │                     │
   │               │ buffer.append(user)│                     │
   │               │                    │                     │
   │               │ 1) chitchat 판정   │                     │
   │               │ asyncio.to_thread()├────────────────────►│
   │               │                    │ "True" / "False"    │
   │               │                    │◄────────────────────┤
   │               │                                          │
   │               │ ┌─ True (일상 대화) ──────────────────┐  │
   │               │ │  chitchat output 프롬프트로         │  │
   │               │ │  history + user → LLM 답변 생성     │  │
   │               │ └──────────────────────────────────────┘ │
   │               │                                          │
   │               │ ┌─ False (정보 요청) ─────────────────┐  │
   │               │ │  AgentExecutor.ainvoke({input})     │  │
   │               │ │  ReAct: tool 선택 → 호출 → 관찰     │  │
   │               │ │  └─ use_db_tool ───► Qdrant 검색    │  │
   │               │ │  └─ use_web_tool ──► SerpAPI 호출   │  │
   │               │ │                                      │  │
   │               │ │  result output 프롬프트로            │  │
   │               │ │  context + history + user → 최종 답  │  │
   │               │ └──────────────────────────────────────┘ │
   │               │                                          │
   │               │ buffer.append(assistant)                 │
   │ { data }      │                                          │
   │◄──────────────┤                                          │
```

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
[Groq LLM 1차 추론]
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
       │   → qdrant.query_points(board_notice, top_k=3)
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

### 임베딩 파이프라인 (Celery)

```
[Celery Worker]              [storage]               [Qdrant]
       │                         │                      │
       │ embed_notice_board()    │                      │
       │ ───────────────────────►│                      │
       │  notices 로드           │                      │
       │  (storage/embedding/board/notice.py)
       │                         │                      │
       │  for each notice:                              │
       │    RecursiveCharacterTextSplitter              │
       │      (chunk_size=100, chunk_overlap=10)        │
       │    SentenceTransformer.encode                  │
       │      (all-MiniLM-L6-v2 → 384-dim)              │
       │                                                │
       │  PointStruct(id, vector, payload)              │
       │  qdrant.upsert(board_notice) ─────────────────►│
       │                                                │
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
- **langsmith** 0.3.45 (보수적 핀 — 0.4+ 부터 `hub.pull` 시 dangerously_pull_public_prompt 게이트 추가)
- **Groq SDK** + 모델: `llama-3.1-8b-instant` (temperature 0.6)

### 임베딩 / 벡터 검색
- **sentence-transformers** 5.4.1 (`all-MiniLM-L6-v2`, 384차원, Cosine 거리)
- **qdrant-client** 1.17.1 (Qdrant 서버 v1.15.4)
- **huggingface-hub** 0.35.0

### 외부 검색
- **google-search-results** 2.4.2 (SerpAPI, langchain_community SerpAPIWrapper)

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
│   │           └── router.py           # POST /api/v1/chat
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
│   │   │   └── groq.py                 # Groq 래퍼 (ChatGroq + run / get_chat_model)
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
│   │   ├── base.py                     # BaseResponse 제네릭
│   │   └── chat/
│   │       ├── request.py              # ChatAgentRequest
│   │       └── response.py             # ChatAgentResponse
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

## 도메인 상세

### 1) Chitchat 판정 (`ChatAgentService.run_chat_agent` 1단계)

사용자 입력을 단기 메모리에 append 한 뒤, **첫 LLM 호출**로 일상 대화 여부를 분류합니다.

- 시스템 프롬프트: `CHAT_PROMPTS['chitchat']['confirm']`
  - 도매꾹 서비스·기능·정책·계정·주문·배송 관련 질문 → `False`
  - 인사·감정 표현·잡담·추천 요청 → `True`
  - 출력은 반드시 Python Boolean 문자열(`True` / `False`)만 허용
- `asyncio.to_thread`로 동기 LLM 호출을 워커 스레드 위임 → 이벤트 루프 보호
- `is_chitchat(output)` 이 `True` 면 일상 대화 분기로, 그렇지 않으면 ReAct 분기로

### 2) Chitchat 답변 (일상 대화 분기)

- 시스템 프롬프트: `CHAT_PROMPTS['chitchat']['output']`
- 단기 메모리 history + 사용자 입력 → 친근한 한국어 + 이모지 응답 생성

### 3) ReAct 에이전트 (정보 요청 분기)

`AgentExecutor.ainvoke({"input": ...})` 호출:

- `agent` = `create_react_agent(llm, tools, prompt=hub.pull("hwchase17/react"))`
  - REACT_PROMPT 는 모듈 로드 시 1회만 fetch (네트워크 I/O 회피)
- `max_iterations=1` — 1회 도구 호출 후 종료
- `handle_parsing_errors=True` — LLM이 ReAct 포맷 위반해도 graceful 처리
- `return_intermediate_steps=True` — 도구 결과 추출용

도구는 **클로저 팩토리**(`build_db_search` / `build_web_search`)로 주입됩니다:

```python
@tool
def use_db_tool(query: str) -> str:
    return db_search.search_qdrant(query)
```

description 이 LLM에게 도구 선택의 단서가 되므로, 도구 추가 시 description 작성이 중요.

### 4) 도구 — DB 검색 (`use_db_tool`)

- `SentenceTransformer` (`all-MiniLM-L6-v2`)로 query 임베딩 (384차원, Cosine)
- Qdrant `board_notice` 컬렉션에서 top-k 유사 청크 검색
- 청크 텍스트를 LLM 컨텍스트로 반환

### 5) 도구 — 웹 검색 (`use_web_tool`)

- `SerpAPIWrapper`(engine=`google`, `hl=ko`, `gl=kr`) 로 검색
- 결과 파싱:
  - `knowledge_graph.description` (있으면 우선)
  - `organic_results[:3]` 의 `snippet` 만 추출
- 결과 없으면 `"No results found."` 반환

> **주의**: 현재 `Serp.run()` 은 실제 API 호출 대신 `storage/serp/response.json` 의 **샘플 응답을 반환**합니다 (`_load_sample_response`). 환경 플래그로 분기 필요.

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

---

## 임베딩 파이프라인 (Celery)

`app/worker/tasks/embedding.py` 의 `embed_notice_board` 태스크는 `storage/embedding/board/notice.py` 의 공지 데이터를 분할·임베딩 후 Qdrant에 저장합니다.

### 처리 흐름

1. **공지 로드**: `storage/embedding/board/notice.py` 의 데이터를 `app/infrastructure/storage/board.py` 로 불러옴
2. **텍스트 분할**: `RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)` 로 청크 생성
3. **임베딩**: `SentenceTransformer.encode` 로 청크당 384차원 벡터 생성
4. **PointStruct 생성**: `id=uuid4`, `vector=[...]`, `payload={chunk_text, source, ...}`
5. **Qdrant 저장**: `board_notice` 컬렉션에 upsert

### 실행 (Flower 또는 CLI)

```bash
# Flower 웹 UI에서 직접 태스크 호출 → http://localhost:5555

# 또는 CLI
celery -A app.worker.celery_app call app.worker.tasks.embedding.embed_notice_board
```

> **사전 조건**: Qdrant `board_notice` 컬렉션이 다음 설정으로 사전 생성되어야 합니다:
> ```python
> vectors_config={"size": 384, "distance": "Cosine"}
> ```

---

## 남은 제한 사항 & 다음 단계

### 현재 제한 사항

| 항목 | 상태 | 설명 |
|---|---|---|
| **단기 메모리 누적** | ⚠️ | `ChatAgentService` 가 매 요청마다 새로 생성되어 `ShortTermMemory.buffer` 가 비어 있음. 단순 싱글톤은 사용자 섞임 위험 (`docs/01 refactoring.md` #4) |
| **Qdrant 컬렉션 자동 생성** | ❌ | `board_notice` 컬렉션을 사전 생성 필요 (`size=384, distance=Cosine`). lifespan 보강 필요 |
| **SerpAPI 샘플 응답 하드코딩** | ⚠️ | `Serp.run()` 이 실제 API 호출 대신 `storage/serp/response.json` 만 반환. 환경 플래그로 분기 필요 (`docs/01 refactoring.md` #11) |
| **응답 스키마 일치성** | ⚠️ | `ChatAgentResponse` 스키마 정의 및 `response_model` 지정 미흡 (`#7`, `#8`) |
| **Config 깊은 dict** | ⚠️ | `EmbeddingModel.MODELS['hugging_face']['sentence_transformer']['All-MiniLM-L6-v2']['name']` 같은 깊은 키 접근. 오타 시 런타임 KeyError, IDE 자동완성 미지원 (`docs/01 refactoring.md` #12) |
| **테스트 커버리지** | ❌ | `tests/`에 샘플만 있고 실질 커버리지 없음 |
| **max_iterations=1** | ⚠️ | ReAct 가 도구 호출 1회만 가능. 복잡한 질의(DB + Web 동시)는 처리 불가 |

### 권장 다음 단계

1. **세션 메모리**: `ChatAgentRequest` 에 `session_id` 추가 + `ShortTermMemoryStore`(`session_id → deque`) 도입 (`#4`)
2. **handle_agent 반환 표준화**: `str` 반환 + 라우터에서 `success_response` 래핑 (`#7`)
3. **응답 스키마**: `ChatAgentResponse` 정의 후 `response_model` 지정 (`#8`)
4. **lifespan 보강**: `client.collection_exists("board_notice")` → 없으면 `create_collection()` 자동 생성
5. **SerpAPI 환경 분기**: `APP_ENV=local` 일 때만 샘플 응답, 그 외 실제 API 호출
6. **Config 평탄화**: 깊은 dict 대신 명시적 dataclass 또는 pydantic settings 필드로 분리
7. **테스트**: 라우터·서비스 단위 테스트 (`app.dependency_overrides` 활용)

---

## 실행 화면

![챗봇 UI](storage/screenshots/ui.png)
![웹 검색](storage/screenshots/web_search.png)
![벡터DB 검색](storage/screenshots/db_search.png)
![실행 화면](storage/screenshots/chatbot_v2.gif)