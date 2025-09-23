""" from fastapi import APIRouter
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AdamW
from sklearn.preprocessing import LabelEncoder
import torch
from torch.utils.data import DataLoader
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from qdrant_client.models import Filter, FieldCondition, MatchValue
from langchain.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceEmbeddings

router = APIRouter(prefix="/ai-agent", tags=["AI-Agent"])

# -----------------------------
# 글로벌 객체
# -----------------------------
client: QdrantClient = None
vectorstore: Qdrant = None
model: AutoModelForSequenceClassification = None
tokenizer: AutoTokenizer = None
le: LabelEncoder = None

# -----------------------------
# 예시 문서
# -----------------------------
docs = [
    {"text": "불이 나면 119에 신고하세요.", "category": "긴급"},
    {"text": "Python 설치 방법: Python을 설치하고 환경 변수를 설정합니다.", "category": "개발"},
    {"text": "VSCode 설치 및 설정: VSCode 설치 후 Python 플러그인을 설치합니다.", "category": "개발"},
    {"text": "위급 상황이 발생하면 112에 신고하세요.", "category": "긴급"},
    {"text": "GIT 설치 및 설정: GIT을 설치하고 원격 repository 에서 소스코드를 clone합니다.", "category": "개발"}
]

# -----------------------------
# Startup 이벤트: 모델 학습 + Qdrant 초기화
# -----------------------------
@router.on_event("startup")
def startup_event():
    global client, vectorstore, model, tokenizer, le

    # --- 1️⃣ LabelEncoder & Dataset 준비 ---
    le = LabelEncoder()
    labels = le.fit_transform([d["category"] for d in docs])
    for i, d in enumerate(docs):
        d["label"] = labels[i]

    dataset = Dataset.from_list(docs)

    # --- 2️⃣ 토크나이저 & 모델 정의 ---
    model_name = "klue/bert-base"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, num_labels=len(le.classes_)
    )

    # --- 3️⃣ 토큰화 ---
    def tokenize(batch):
        return tokenizer(batch["text"], padding=True, truncation=True)
    dataset = dataset.map(tokenize, batched=True)
    dataset.set_format("torch", columns=["input_ids", "attention_mask", "label"])

    dataloader = DataLoader(dataset, batch_size=2, shuffle=True)

    # --- 4️⃣ 옵티마이저 정의 & 학습 ---
    optimizer = AdamW(model.parameters(), lr=5e-5)
    model.train()
    for epoch in range(3):
        for batch in dataloader:
            optimizer.zero_grad()
            outputs = model(
                input_ids=batch["input_ids"],
                attention_mask=batch["attention_mask"],
                labels=batch["label"]
            )
            loss = outputs.loss
            loss.backward()
            optimizer.step()
        print(f"[DEBUG] Epoch {epoch+1} 완료, Loss: {loss.item():.4f}")

    # --- 5️⃣ 모델 저장 ---
    model.save_pretrained("./model")
    tokenizer.save_pretrained("./model")
    model.eval()

    # --- 6️⃣ Qdrant 초기화 ---
    client = QdrantClient(url="http://qdrant:6333")
    client.recreate_collection(
        collection_name="ask",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = Qdrant(client=client, collection_name="ask", embeddings=embeddings)

    # 예시 문서 벡터 저장
    for d in docs:
        vectorstore.add_texts([d["text"]], metadatas=[{"category": d["category"]}])

# -----------------------------
# 질문 처리 API
# -----------------------------
@router.get("/query")
async def query_api(question="", similarity_threshold: float = 0.6):
    # 하드코딩된 질문
    question = "로컬 PC 설정 방법 알려줘"

    # 1️⃣ 카테고리 예측
    inputs = tokenizer(question, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        pred = torch.argmax(outputs.logits, dim=1).item()
        category = le.inverse_transform([pred])[0]

    # 2️⃣ Qdrant 검색
    q_filter = Filter(
        must=[FieldCondition(key="category", match=MatchValue(value=category))]
    )
    results_with_scores = vectorstore.similarity_search_with_score(question, k=10, filter=q_filter)

    # 3️⃣ Cosine similarity 필터링
    filtered_results = []
    for r, distance in results_with_scores:
        similarity = 1 - distance
        if similarity >= similarity_threshold:
            filtered_results.append({"content": r.page_content, "similarity": similarity})
        print(f"[DEBUG] text={r.page_content}, similarity={similarity:.3f}, category={r.metadata['category']}")

    print(f"[DEBUG] 질문='{question}', 예측카테고리='{category}'")
    return {
        "question": question,
        "category": category,
        "results": filtered_results
    }
 """