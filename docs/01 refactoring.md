# fastapi-chatbot 리팩토링 개선안

`fastapi-imageSearch` 의 디렉토리·DI 패턴을 기준으로 `fastapi-chatbot` 의 어색한 부분을 정리한 문서입니다. 우선순위가 높은 항목부터 나열합니다.

---

## ✅ 진행 체크리스트

> 작업하면서 `[ ]` → `[x]` 로 바꿔주세요. 한 항목 안에서도 일부만 끝났으면 `[~]` (in progress) 로 표시.

### P0 — 동작/구조의 핵심
- [x] **#1 Tool DI 화** — `ChatAgentService` 에서 `qdrant`/`embedding_model` 제거, `agent_tools` 주입
  - [x] `core/dependencies/chat.py` 에 `get_db_search`, `get_web_search`, `get_chat_agent_tools` 추가
  - [x] `modules/tools/tool.py` 에 `build_db_search`, `build_web_search` 팩토리
  - [x] `@tool` 함수에 docstring 작성 (`ValueError` 회피)
- [x] **#2 WebSearch 내부 `new` 제거** — `WebSearch(serp, serp_service)` 생성자 주입
  - [ ] (선택) `Serp` 안의 `SerpAPIWrapper` 도 주입으로 분리
- [ ] **#7 라우터 응답 버그 수정** — `handle_agent` 결과를 클라이언트로 반환
  - [ ] `handle_agent` 가 `str`/DTO 반환 (현재 `return True`)
  - [ ] router 가 `success_response(...)` 로 감싸 반환
  - [ ] `GET` → `POST` + body 로 변경

### P1 — 의도한 기능이 동작하게
- [x] **#3 Lifespan 워밍업** — `get_qdrant_client/get_embedding_model/get_groq` preload + 종료 시 close
  - [x] `get_qdrant_client().close()` 괄호 누락 버그 수정
- [ ] **#4 ShortTermMemory 세션별 Store 화**
  - [ ] `ShortTermMemoryStore` (`session_id -> deque`) 클래스 작성
  - [ ] `get_memory_store()` `@lru_cache` 싱글톤 등록
  - [ ] `ChatAgentService` 가 `memory_store` 주입받고 `session_id` 인자 사용
  - [ ] Router 에서 `session_id` 받아 전달 (#8 ChatRequest 와 함께)
  - [ ] (운영) Redis Store 로 승격
- [ ] **#8 Schema 정의** — `app/schemas/chat/{request,response}.py`, `schemas/common.py`

### P2 — 유지보수성/성능
- [ ] **#5 ChatAgentService 분해** — `Classifier` / `ChitchatResponder` / `AgentRunner` 로 분리
- [x] **#6 React Agent 캐싱** — `hub.pull` 1회, `AgentExecutor` 재사용, `Groq.get_chat_model()` getter
  - [x] `REACT_PROMPT` 모듈 레벨 상수화
  - [x] `Groq.get_chat_model()` 추가 + `self._llm` private 화 (#10 부분 해결)
  - [x] `ChatAgentService.__init__` 에서 `agent_executor` 1회 생성 후 재사용
  - [x] `set_agent` 메서드 제거

### P3 — 정리
- [ ] **#9 services 디렉토리 정리** — `services/serp_service.py` → `services/search/serp.py` 또는 `modules/search/` ✅ 이미 이동 완료
- [x] services/search 로 이동 완료 (#9 일부)
- [x] **#10 Groq leaky abstraction 제거** — `self.llm.llm` 접근 제거 (#6 작업 중 함께 해결)
- [ ] **#11 Serp 샘플/실호출 플래그화** — `config.SERP_USE_SAMPLE`
- [ ] **#12 Config dataclass 화** — `LLMModel.MODELS[...]` 깊은 dict 제거
- [ ] **#13 Worker DI 일원화** — `core/dependencies/factory.py` 도입
- [ ] **#14 잡다한 정리**
  - [ ] (a) stray 파일 정리 (`storage/vectordb/data/dev_____/...`)
  - [ ] (b) `print` → `logger`
  - [ ] (d) `STORAGE_PATH` 중복 계산 제거
  - [ ] (e) `is_chitchat` 비교 견고화
  - [ ] (f) `agent_output` 타입 정규화
  - [ ] (g) `requirements.txt` 제거 (`pyproject.toml` 단일화)
  - [ ] (h) 단위 테스트 추가

### 검증 (각 작업 후 확인)
- [ ] 컨테이너 재시작 시 lifespan 워밍업 로그 정상
- [ ] `/api/v1/chat/` 호출 시 실제 LLM 답변이 응답 body 에 들어감
- [ ] 같은 `session_id` 로 두 번 요청 시 두 번째 요청에서 첫 번째 대화가 history 에 포함됨
- [ ] 다른 `session_id` 두 개로 요청 시 history 가 섞이지 않음
- [ ] `/docs` (Swagger) 에 `ChatRequest`/`ChatResponse` 스키마 노출
- [ ] 워커가 `embed_notice_board` 태스크 정상 처리

---

## 1. Tool 이 DI 로 주입되지 않는다 (가장 큰 이슈)

### 현재 코드
```python
# app/services/agent/chat.py:60
tools = get_tools(self.qdrant, self.embedding_model)
result = await self.set_agent(tools).ainvoke({"input": user_input})
```
```python
# app/modules/tools/tools.py
def get_tools(qdrant, embedding_model):
    db_search = DBSearch(qdrant, embedding_model)
    web_search = WebSearch()
    @tool
    def search_db_tool(query: str): ...
    @tool
    def search_web_tool(query: str): ...
    return [search_web_tool, search_db_tool]
```

### 문제점
- **요청마다 Tool 객체가 재생성**된다 (`DBSearch`, `WebSearch`, 내부의 `Serp`, `SerpService` 모두 매번 `__init__`).
- `ChatAgentService` 가 자기 책임도 아닌 `qdrant`, `embedding_model` 을 들고 있는 이유가 **단지 Tool 에 넘겨주기 위해서**다 — 전형적인 leaky abstraction (DBSearch 의존성이 ChatAgentService 의 시그니처를 오염시킴).
- Tool 을 추가/교체하려면 `ChatAgentService` 시그니처와 `get_tools` 시그니처를 동시에 수정해야 함 → OCP 위반.
- 테스트에서 Tool 만 mock 하기 어렵다 (가짜 `qdrant`/`embedding_model` 까지 만들어야 함).
- `WebSearch` 는 내부에서 `Serp()`, `SerpService()` 를 직접 `new` 하므로 DI 사슬이 끊어진다.

### 해결방안
imageSearch 의 `FruitSearchService(fruit_point_service)` 처럼 **Service 는 자기보다 한 단계 하위 객체(Tool 목록)만 받게** 하고, Tool 의 내부 의존성은 `core/dependencies/` 에서 조립한다.

```python
# app/core/dependencies/chat.py
from fastapi import Depends
from langchain_core.tools import BaseTool

from app.core.dependencies.common import get_embedding_model, get_groq, get_qdrant
from app.modules.tools.db_search import DBSearch
from app.modules.tools.web_search import WebSearch
from app.modules.tools.tools import build_db_tool, build_web_tool


def get_db_search(qdrant=Depends(get_qdrant), embedding_model=Depends(get_embedding_model)) -> DBSearch:
    return DBSearch(qdrant, embedding_model)

def get_web_search(serp=Depends(get_serp), serp_service=Depends(get_serp_service)) -> WebSearch:
    return WebSearch(serp, serp_service)

def get_chat_tools(
    db_search: DBSearch = Depends(get_db_search),
    web_search: WebSearch = Depends(get_web_search),
) -> list[BaseTool]:
    return [build_db_tool(db_search), build_web_tool(web_search)]

def get_chat_agent_service(
    llm: Groq = Depends(get_groq),
    tools: list[BaseTool] = Depends(get_chat_tools),
    memory: ShortTermMemory = Depends(get_short_term_memory),
) -> ChatAgentService:
    return ChatAgentService(llm, tools, memory)
```

```python
# app/modules/tools/tools.py — 팩토리 함수만 노출
from langchain_core.tools import tool
from app.modules.tools.db_search import DBSearch
from app.modules.tools.web_search import WebSearch

def build_db_tool(db_search: DBSearch):
    @tool
    def search_db_tool(query: str) -> str:
        """도매꾹과 관련된 모든 정보 검색에 사용."""
        return db_search.search_qdrant(query)
    return search_db_tool

def build_web_tool(web_search: WebSearch):
    @tool
    def search_web_tool(query: str) -> str:
        """도매꾹을 제외한 정보 검색에 사용."""
        return web_search.search_serp(query)
    return search_web_tool
```

```python
# app/services/agent/chat.py — qdrant/embedding_model 의존성 제거
class ChatAgentService:
    def __init__(self, llm: Groq, tools: list, memory: ShortTermMemory):
        self.llm = llm
        self.tools = tools
        self.short_term_memory = memory
```

> 효과: ChatAgentService 는 LLM·Tool·Memory 만 안다. Tool 의 내부 구조(qdrant 사용 여부 등)가 바뀌어도 Service 시그니처는 그대로.

---

## 2. `WebSearch` 내부 `new` 남발 (DI 깨짐)

### 현재 코드
```python
# app/modules/tools/web_search.py
class WebSearch:
    def __init__(self):
        self.serp = Serp()                    # 내부에서 또 SerpService() 생성

    def search_serp(self, query: str) -> str:
        serp_service = SerpService()          # 메서드 안에서 또 생성
        response = self.serp.run(query)
        parsed = serp_service.parse_serp(response)
```

### 문제점
- `Serp` 가 이미 내부에 `SerpService` 를 들고 있는데 `WebSearch.search_serp` 가 **또** 만들어 쓴다 — 중복/혼란.
- 외부에서 `Serp`/`SerpService` 를 mock 하거나 fake 로 교체할 수 없다.

### 해결방안
- `Serp` 와 `SerpService` 를 생성자 주입으로 받게 변경.
- `Serp` 안의 `self.serp_service = SerpService()` 도 주입으로 받게 한다.
- `core/dependencies/common.py` 에 `get_serp`, `get_serp_service` 추가하고 `@lru_cache` 로 싱글톤화.

```python
class WebSearch:
    def __init__(self, serp: Serp, serp_service: SerpService):
        self.serp = serp
        self.serp_service = serp_service

    def search_serp(self, query: str) -> str:
        response = self.serp.run(query)
        return "\n".join(self.serp_service.parse_serp(response))
```

---

## 3. Lifespan 에서 모델 워밍업이 없다

### 현재 코드
```python
# app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield
```

### 문제점
- imageSearch 는 `get_qdrant_client()`, `get_embedding_model()`, `get_yolo_model()` 를 lifespan 에서 미리 호출해 **콜드 스타트를 방지**한다.
- 챗봇은 첫 `/chat` 요청 시 SentenceTransformer 다운로드/로드 + Groq 초기화가 모두 실행돼 응답이 수 초~수십 초 지연.
- 종료 시 `qdrant.close()` 도 없어 커넥션 누수 가능.

### 해결방안
```python
from app.core.dependencies.common import get_qdrant_client, get_embedding_model, get_groq

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    get_qdrant_client()
    get_embedding_model()
    get_groq()
    yield
    get_qdrant_client().close()
```

---

## 4. `ShortTermMemory` 가 요청마다 새로 생성됨 → 메모리 의미 상실

### 현재 코드
```python
# app/services/agent/chat.py:20
class ChatAgentService:
    def __init__(self, qdrant, embedding_model, llm):
        ...
        self.short_term_memory = ShortTermMemory()
```
`get_chat_agent_service` 는 `@lru_cache` 없이 매 요청마다 `ChatAgentService` 를 새로 만든다. 결과적으로 `ShortTermMemory.buffer` 도 매번 비어 있는 deque 가 되어 **대화 히스토리가 누적되지 않는다**.

### 왜 단순 싱글톤(`@lru_cache`)으로는 안 되는가
프로세스 단위로 1개의 `ShortTermMemory` 를 공유하면, **모든 사용자의 대화가 같은 deque(`maxlen=10`)에 섞인다.**
- 사용자 A 가 5번 말하고 사용자 B 가 5번 말하면, 다음 요청 때 둘이 서로의 발화를 history 로 받게 됨.
- 동시 요청 시 deque 의 race condition 도 우려.
- 즉, "같은 대화 누적" 의도라면 **단위가 프로세스가 아니라 세션(사용자)** 이어야 한다.

### 해결방안 — 세션별 Store 패턴

`session_id` 를 키로 한 메모리 저장소를 **하나의 싱글톤**으로 두고, 각 세션의 buffer 는 그 안에서 분리한다.

```python
# app/modules/memory/short_term.py
from collections import deque
from threading import Lock


class ShortTermMemoryStore:
    """session_id 별로 분리된 단기 메모리 저장소."""
    def __init__(self, max_messages: int = 10):
        self._max = max_messages
        self._store: dict[str, deque] = {}
        self._lock = Lock()

    def _get_buffer(self, session_id: str) -> deque:
        with self._lock:
            if session_id not in self._store:
                self._store[session_id] = deque(maxlen=self._max)
            return self._store[session_id]

    def append(self, session_id: str, role: str, content: str) -> None:
        self._get_buffer(session_id).append({"role": role, "content": content})

    def format_history(self, session_id: str) -> str:
        return "\n".join(
            f"{m['role']}: {m['content']}" for m in self._get_buffer(session_id)
        )
```

```python
# app/core/dependencies/common.py
@lru_cache(maxsize=1)
def get_memory_store() -> ShortTermMemoryStore:
    return ShortTermMemoryStore(max_messages=10)
```

```python
# app/core/dependencies/chat.py
def get_chat_agent_service(
    agent_tools = Depends(get_chat_agent_tools),
    llm: Groq = Depends(get_groq),
    memory_store: ShortTermMemoryStore = Depends(get_memory_store),
) -> ChatAgentService:
    return ChatAgentService(agent_tools, llm, memory_store)
```

```python
# app/services/agent/chat.py
class ChatAgentService:
    def __init__(self, agent_tools, llm, memory_store: ShortTermMemoryStore):
        self.agent_tools = agent_tools
        self.llm = llm
        self.memory_store = memory_store

    async def handle_agent(self, user_input: str, session_id: str):
        self.memory_store.append(session_id, "user", user_input)
        history = self.memory_store.format_history(session_id)
        ...
        self.memory_store.append(session_id, "assistant", agent_output)
```

```python
# app/schemas/chat/request.py
class ChatRequest(BaseModel):
    query: str
    session_id: str   # 클라이언트가 대화 단위 UUID 발급

# app/api/v1/chat/router.py
@router.post('/', response_model=ChatResponse)
async def chat(req: ChatRequest, service: ChatAgentService = Depends(get_chat_agent_service)):
    result = await service.handle_agent(req.query, req.session_id)
    return success_response({"answer": result})
```

### `session_id` 발급 방식 (선택)

| 방식 | 설명 | 적합한 경우 |
|------|------|-----------|
| 클라이언트가 UUID 생성 후 요청마다 동봉 | 가장 단순 | 익명 채팅 위젯 |
| 로그인 사용자 ID + 대화 ID | "새 대화" 시작 시 새 conversation_id 발급 | 로그인 기반 서비스 (도매꾹) |
| 쿠키 (`session` 미들웨어) 자동 발급 | 서버가 발급 | 웹 임베디드 |

도매꾹처럼 로그인 기반이면 `f"{user_id}:{conversation_id}"` 조합 추천.

### 운영 시 한 단계 더 — Redis Store (선택)

단일 프로세스 dict 는 **워커 여러 개 / 재시작 시 메모리 소실** 이 한계. 이미 Celery broker 로 Redis 를 쓰므로(`config.CELERY_BROKER_URL`) 같은 인스턴스를 활용 가능.

```python
class RedisShortTermMemoryStore:
    def __init__(self, redis_client, ttl: int = 3600, max_messages: int = 10):
        self.redis = redis_client
        self.ttl = ttl
        self.max = max_messages

    async def append(self, session_id: str, role: str, content: str):
        key = f"chat:memory:{session_id}"
        await self.redis.rpush(key, json.dumps({"role": role, "content": content}))
        await self.redis.ltrim(key, -self.max, -1)   # 최근 N개만 보존
        await self.redis.expire(key, self.ttl)        # 비활성 세션 자동 만료

    async def format_history(self, session_id: str) -> str:
        items = await self.redis.lrange(f"chat:memory:{session_id}", 0, -1)
        msgs = [json.loads(i) for i in items]
        return "\n".join(f"{m['role']}: {m['content']}" for m in msgs)
```

`ShortTermMemoryStore` 와 동일한 인터페이스(`append`, `format_history`) 로 만들어두면 in-memory ↔ Redis 교체가 의존성 한 줄 변경으로 끝남.

### 옵션 비교

| 옵션 | 같은 대화 누적 | 사용자 분리 | 재시작 유지 | 멀티 워커 |
|------|:---:|:---:|:---:|:---:|
| 매 요청 새로 생성 (현재) | ❌ | — | — | — |
| 프로세스 싱글톤 (`@lru_cache` 단일 객체) | ✅ | ❌ | ❌ | ❌ |
| **세션별 in-memory Store** | ✅ | ✅ | ❌ | ❌ |
| **세션별 Redis Store** | ✅ | ✅ | ✅ | ✅ |

→ 도매꾹 채팅 의도("같은 대화 누적, 사용자 안 섞임")에는 **세션별 in-memory Store** 가 최소 정답. 운영 단계로 가면 Redis Store 로 승격.

---

## 5. `ChatAgentService` 가 너무 많은 책임을 가짐 (SRP 위반)

`handle_agent` 한 메서드가:
1. 메모리 append
2. chitchat 분류용 LLM 호출
3. 분기
4. (chitchat) 응답 생성
5. (search) Tool 조립 + Agent 생성 + Agent 실행 + 결과 가공
6. 응답 LLM 호출
7. 메모리 append

…을 전부 한다.

### 해결방안 (계층 분리 제안)
- `ChatClassifier` — chitchat 여부 판단만 담당
- `ChitchatResponder` — chitchat 응답 생성
- `AgentRunner` — `set_agent` + Tool 실행 + intermediate_steps 정리
- `ChatAgentService` — 위 세 컴포넌트를 조립해서 흐름만 제어

각 컴포넌트도 DI 로 주입한다. 그러면 chitchat 로직만 바꾸거나 Agent 종류를 ReAct → OpenAI Functions Agent 로 교체하기 쉽다.

---

## 6. React Agent 가 요청마다 재생성 ✅

### 현재 코드 (수정 전)
```python
def set_agent(self, tools, max_iterations=1):
    react_prompt = hub.pull("hwchase17/react")   # 매번 hub 호출
    agent = create_react_agent(llm=self.llm.llm, tools=tools, prompt=react_prompt)
    ...
```

### 문제점
- `hub.pull` 은 네트워크/디스크 I/O 가 있을 수 있는 호출 — 매 요청마다 호출하면 비용/지연.
- `self.llm.llm` 으로 래퍼 내부 객체를 꺼내 쓰는 것도 leaky (#10 도 함께 해결).

### 해결방안 (적용 완료)

**① `hub.pull` 모듈 레벨 캐싱**
```python
# app/services/agent/chat.py
REACT_PROMPT = hub.pull("hwchase17/react")   # 모듈 import 시 1회
```

**② `Groq.get_chat_model()` getter — leaky `self.llm.llm` 제거**
```python
# app/modules/llm/groq.py
class Groq:
    def __init__(self):
        self._llm = ChatGroq(...)            # private 으로 변경

    def get_chat_model(self) -> ChatGroq:
        return self._llm
```

**③ `AgentExecutor` 를 `__init__` 에서 1회만 생성**
```python
class ChatAgentService:
    def __init__(self, agent_tools, llm, max_iterations: int = 1):
        self.agent_tools = agent_tools
        self.llm = llm
        self.short_term_memory = ShortTermMemory()
        self.agent_executor = self._build_agent_executor(max_iterations)

    def _build_agent_executor(self, max_iterations):
        agent = create_react_agent(
            llm=self.llm.get_chat_model(),
            tools=self.agent_tools,
            prompt=REACT_PROMPT,
        )
        return AgentExecutor.from_agent_and_tools(
            agent=agent, tools=self.agent_tools,
            verbose=True, max_iterations=max_iterations,
            handle_parsing_errors=True, return_intermediate_steps=True,
        )

    async def handle_agent(...):
        ...
        result = await self.agent_executor.ainvoke({"input": user_input})  # 캐시된 executor 재사용
```

### 효과
- `hub.pull` 호출: 요청당 1회 → 프로세스당 1회
- `AgentExecutor` 생성: 요청당 1회 → 요청당 0회 (init 시 1회만)
- `Groq` 의 내부 `ChatGroq` 인스턴스가 외부로 노출되지 않음

### 주의
- `ChatAgentService` 가 `get_chat_agent_service` 에서 매 요청 새로 생성되면 `__init__` 의 1회 캐싱 효과가 사라짐. 따라서 #4 (Memory Store 외부화) 이후 `ChatAgentService` 자체를 `@lru_cache` 싱글톤으로 만들면 완전한 1회 캐싱이 된다.
  - `ChatAgentService` 가 stateless (메모리를 Store 로 분리) 가 되면 안전하게 싱글톤화 가능.

---

## 7. 라우터가 실제 응답을 반환하지 않음 (버그)

### 현재 코드
```python
# app/api/v1/chat/router.py
@router.get('/')
async def index(query, chat_agent_service = Depends(get_chat_agent_service)):
    await chat_agent_service.handle_agent(query)
    return {"message": "Hello AI-Agent"}    # ← 결과 무시
```
```python
# app/services/agent/chat.py
return True
# return success_response(agent_output)   # ← 주석 처리됨
```

### 문제점
- 에이전트가 생성한 답변이 클라이언트에 전혀 전달되지 않는다.
- 채팅 API 가 `GET` 이고 `query` 가 query string 인 것도 어색. POST + body 가 일반적.

### 해결방안
- `handle_agent` 가 `str` (또는 응답 DTO) 를 반환.
- Router 가 `success_response(jsonable_encoder(result))` 로 감싸 반환.
- imageSearch 처럼 `app/schemas/chat/response.py` 에 `ChatResponse` Pydantic 모델 정의 후 `response_model` 로 지정.

```python
@router.post('/', response_model=ChatResponse)
async def chat(req: ChatRequest, service: ChatAgentService = Depends(get_chat_agent_service)):
    result = await service.handle_agent(req.query)
    return success_response(jsonable_encoder(result))
```

---

## 8. `app/schemas/` 가 비어 있음

imageSearch 는 `schemas/image_search/response.py` 에 응답 스키마가 있는데 chatbot 은 비어 있다.

### 해결방안
- `app/schemas/chat/request.py` — `ChatRequest(query: str, session_id: str | None)`
- `app/schemas/chat/response.py` — `ChatResponse(answer: str, sources: list[str] | None)`
- `app/schemas/common.py` — 공통 응답 envelope (imageSearch 와 동일하게)

---

## 9. `services/` 디렉토리 구조 불일치

```
services/
├── agent/chat.py         ← 폴더 네임스페이스
├── point/notice_board.py ← 폴더 네임스페이스
└── serp_service.py       ← flat (어색)
```

### 해결방안
`serp_service.py` 를 다른 두 서비스와 톤을 맞춘다. 두 가지 선택지:
- **a) `app/services/search/serp.py`** 로 이동 (services 계층에 두려면)
- **b) `app/modules/search/serp_service.py`** 로 이동 — 사실 SerpService 는 외부 API 결과 파싱 유틸에 가깝고, `Serp` 와 짝을 이루므로 **이쪽이 더 자연스럽다**. imageSearch 에서 `services/` 는 "유스케이스" 계층인데 SerpService 는 유스케이스라기보다 어댑터에 가깝다.

---

## 10. `Groq` 래퍼의 leaky abstraction

```python
# 외부에서 내부 ChatGroq 인스턴스를 직접 꺼내 씀
agent = create_react_agent(llm=self.llm.llm, ...)
```

### 해결방안
- 명시적 getter 추가: `def get_chat_model(self) -> ChatGroq: return self._llm`
- 또는 `Groq` 가 LangChain Runnable 인터페이스를 그대로 노출 (`__or__` 등 위임)

---

## 11. `Serp.run` 이 항상 샘플 JSON 만 로드

```python
def run(self, query):
    # return self.serp.results(query)
    return self.load_sample_response()
```

### 해결방안
- 개발/테스트용이라면 `config.SERP_USE_SAMPLE: bool` 플래그로 분기.
- 또는 `FakeSerp` / `RealSerp` 두 구현으로 나누고 DI 단계에서 선택.

```python
# core/dependencies/common.py
def get_serp() -> Serp:
    return FakeSerp() if config.SERP_USE_SAMPLE else RealSerp()
```

---

## 12. `config/llm_model.py`, `config/embedding_model.py` 의 깊은 dict

```python
LLMModel.MODELS['llama']['3.1-8b-instant']['model']
EmbeddingModel.MODELS['hugging_face']['sentence_transformer']['All-MiniLM-L6-v2']['name']
```

### 문제점
- 키 오타 시 런타임 KeyError, IDE 자동완성 안 됨.
- `temperature`, `timeout`, `max_tokens` 같은 필드가 정의돼 있지만 `Groq.__init__` 에서 `timeout`/`max_tokens` 는 사용되지 않음.

### 해결방안
- Pydantic `BaseModel` 또는 dataclass 로 정의.
- 또는 Enum + dataclass 조합.

```python
@dataclass(frozen=True)
class LLMConfig:
    model: str
    temperature: float
    timeout: int
    max_tokens: int

LLAMA_3_1_8B = LLMConfig(model="llama-3.1-8b-instant", temperature=0.6, timeout=10, max_tokens=1000)
```

---

## 13. Worker task 가 DI 컨테이너를 우회

### 현재 코드
```python
# app/worker/tasks/embedding.py
@celery.task
def embed_notice_board():
    notice_board_service = NoticeBoardPointService(
        qdrant=Qdrant(get_qdrant_client()),
        embedding_model=get_embedding_model()
    )
    notice_board_service.embed_notice_board()
```

imageSearch 도 같은 패턴이라 일관성은 있지만, `Qdrant(get_qdrant_client())` 를 직접 조립하는 것은 `core/dependencies/common.get_qdrant()` 와 중복.

### 해결방안
Celery 는 FastAPI `Depends` 를 못 쓰므로, 순수 함수 형태의 조립자를 별도로 만들고 워커/엔드포인트가 공유한다.

```python
# app/core/dependencies/factory.py
def build_notice_board_service() -> NoticeBoardPointService:
    return NoticeBoardPointService(
        qdrant=Qdrant(get_qdrant_client()),
        embedding_model=get_embedding_model(),
    )

# worker
@celery.task
def embed_notice_board():
    return build_notice_board_service().embed_notice_board()

# dependencies/notice.py (FastAPI 쪽)
def get_notice_board_service() -> NoticeBoardPointService:
    return build_notice_board_service()
```

---

## 14. 잡다한 정리거리

| # | 위치 | 문제 | 권장 |
|---|------|------|------|
| a | `storage/vectordb/data/dev_____/openapi.py`, `storage/vectordb/data/base.py` | 출처 불명 stray 파일 (앱 어디서도 import 안 함) | 삭제 또는 별도 폴더로 격리 |
| b | `app/api/__init__.py`, `app/api/v1/__init__.py` | `print(...)` 로 import 실패 로깅 | `logging.getLogger(__name__).error(...)` 사용 |
| c | `app/api/v1/chat/__init__.py` | 빈 파일 | imageSearch 와 동일하므로 그대로 두되 의도 명시 |
| d | `app/core/config.py:24` | `STORAGE_PATH` 를 모듈 레벨에서 한 번 더 계산 (`Config` 안에도 있음) | `Config` 의 computed field 로 통합 |
| e | `app/services/agent/chat.py` `is_chitchat` | LLM 출력 문자열 비교 `chitchat_output == "True"` — 공백/케이스에 취약 | `.strip().lower() == "true"` |
| f | `app/services/agent/chat.py` 의 `agent_output = getattr(agent_output, "content", "")` | chitchat 분기에선 `AIMessage`, search 분기에선 또 변환 — 분기마다 타입 다름 | 각 브랜치에서 동일하게 `str` 로 정규화 |
| g | `requirements.txt` 와 `pyproject.toml` 양립 (imageSearch 는 `pyproject.toml` 만) | 의존성 중복 관리 | `pyproject.toml` + `uv.lock` 만 사용 |
| h | `tests/test_sample.py` 만 존재 | 실제 단위 테스트 부재 | DI 가 정돈된 후 Service 단위 테스트부터 추가 |

---

## 우선순위 요약

| 순위 | 항목 | 영향 |
|------|------|------|
| P0 | Tool DI 화 (#1, #2) | 구조의 핵심. 이후 작업 전제. |
| P0 | 라우터 응답 버그 수정 (#7) | 기능 자체가 동작 안 함 |
| P1 | Lifespan 워밍업 (#3) | UX (콜드 스타트) |
| P1 | ShortTermMemory 세션별 Store 화 (#4) | 의도된 누적 대화가 동작하지 않음 + 단순 싱글톤은 사용자 섞임 |
| P1 | Schema 정의 (#8) | OpenAPI 문서 + 타입 안전성 |
| P2 | ChatAgentService 분해 (#5) | 유지보수성 |
| P2 | React Agent 캐싱 (#6) | 성능 |
| P3 | Serp 플래그화 (#11) | 환경 분리 |
| P3 | Config dataclass 화 (#12) | 안전성 |
| P3 | Worker DI 일원화 (#13) | 일관성 |
| P3 | 디렉토리 정리·로깅·테스트 (#9, #14) | 정리 |

---

## 리팩토링 후 기대 디렉토리 (요약)

```
app/
├── api/v1/chat/router.py
├── core/
│   ├── dependencies/
│   │   ├── common.py            # qdrant/embedding/llm/serp/memory 싱글톤
│   │   ├── chat.py              # tool 조립 + ChatAgentService 조립
│   │   └── factory.py           # 워커 공용 조립자
│   ├── exceptions/
│   └── utils/
├── infrastructure/
│   ├── storage/board.py
│   └── vectordb/qdrant.py
├── modules/
│   ├── llm/groq.py              # get_chat_model() getter 추가
│   ├── memory/short_term.py
│   ├── prompt/chat.py
│   ├── search/
│   │   ├── serp.py
│   │   └── serp_service.py      # services/ 에서 이동
│   └── tools/
│       ├── db_search.py
│       ├── web_search.py        # 생성자 주입으로 변경
│       └── tools.py             # build_*_tool 팩토리만 남김
├── schemas/
│   └── chat/
│       ├── request.py
│       └── response.py
├── services/
│   └── agent/
│       ├── chat.py              # 흐름 제어만
│       ├── classifier.py        # (분할 시)
│       └── runner.py            # (분할 시)
└── worker/
```
