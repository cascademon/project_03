# 🤖 AI Multi-Agent Review Analysis System

LLM 기반 리뷰 감성 분석 자동화 시스템에  
Supervisor Orchestration, Critic 검증, Human-in-the-Loop(HITL) 구조를 결합하여  
AI 분석의 신뢰성과 품질을 강화한 Multi-Agent Workflow 프로젝트입니다.

사용자가 리뷰 데이터를 입력하면 AI가 리뷰를 분석하고,  
품질 검증 → 재시도 → Human Review까지 자동 수행합니다.

---

# 📌 프로젝트 소개

기존 감성 분석 시스템은 단순히 결과만 출력하는 경우가 많아  
LLM의 다음과 같은 문제를 해결하기 어려웠습니다.

- 잘못된 감정 판단
- 근거 없는 Evidence 생성(Hallucination)
- JSON 구조 오류
- 불안정한 출력 형식
- 애매한 리뷰 분석 실패

본 프로젝트는 이러한 문제를 해결하기 위해  
생성형 AI 기반 Multi-Agent 시스템을 설계하였습니다.

특히,

- Analyzer Agent
- Critic Agent
- Supervisor Agent
- Human-in-the-Loop(HITL)

구조를 통해  
AI 자동화와 Human 품질 검수를 함께 수행하도록 구현하였습니다.

---

# 🚀 주요 기능

## 1️⃣ 리뷰 감성 분석

- Aspect 기반 리뷰 분석
- 긍정 / 부정 감정 분류
- Evidence 추출
- 구조화된 JSON 생성

### Example

```json
{
  "items": [
    {
      "aspect": "배송",
      "label": 0,
      "evidence": "배송이 느려요"
    }
  ]
}
```

---

## 2️⃣ Critic 기반 품질 검증

Analyzer 결과를 AI가 다시 검증합니다.

### 검증 항목

- JSON 구조 오류
- Aspect 적절성
- Evidence 실제 존재 여부
- 감정(Label) 정확성
- 중복 여부

---

## 3️⃣ Reason Code 기반 오류 분류

Critic Agent는 오류를 유형별로 분류합니다.

| Reason Code | 설명 |
|---|---|
| OUTPUT_ERROR | 출력 구조 오류 |
| SCOPE_ERROR | 잘못된 Aspect |
| EVIDENCE_ERROR | Evidence 불일치 |
| QUALITY_ERROR | 감정 판단 애매 |
| ETC | 기타 오류 |
| OK | 정상 |

---

## 4️⃣ Repair Directive 기반 재시도

단순 재실행이 아니라  
오류 원인에 맞는 수정 지시를 생성합니다.

### Example

```python
"EVIDENCE_ERROR":
"evidence는 리뷰 원문에 실제로 있는 연속된 문구만 사용하라."
```

이를 기반으로 Analyzer가 수정된 분석을 다시 수행합니다.

---

## 5️⃣ Supervisor 기반 Workflow 제어

Supervisor Agent가 전체 흐름을 제어합니다.

### 역할

- 다음 Agent 결정
- 재시도 여부 판단
- Human Review 여부 판단
- 최종 종료 제어

즉, 전체 Multi-Agent 시스템의 오케스트레이터 역할을 수행합니다.

---

## 6️⃣ Human-in-the-Loop(HITL)

본 프로젝트의 핵심 기능입니다.

LLM이 다음 상황에 도달하면 사람이 직접 개입합니다.

### Human Review 조건

- 반복 재시도 실패
- 감정 판단이 애매한 경우
- 품질 신뢰성이 낮은 경우

### Example

```python
if retry_count >= 2:
    return True
```

```python
HUMAN_REQUIRED = {
    "QUALITY_ERROR",
    "ETC"
}
```

---

## 7️⃣ Human Review 시스템

Human Reviewer는 다음 정보를 확인할 수 있습니다.

- 리뷰 원문
- 기존 분석 결과
- Critic 평가 결과
- 수정 가이드

이후 사람이 직접 최종 JSON 결과를 수정 및 승인합니다.

---

# 🧠 Agent Workflow 구조

```text
User Review Input
        ↓
Analyzer Agent
(감성 분석)
        ↓
Critic Agent
(품질 검증)
        ↓
Supervisor Agent
(흐름 제어)
   ├─ 정상 → 종료
   ├─ 오류 → 재시도
   └─ 위험/애매 → Human Review(HITL)
```

---

# ⚙️ 기술 스택

## 🔹 AI / LLM

- OpenAI GPT
- Prompt Engineering

### 역할

- 리뷰 감성 분석
- 품질 검증
- 오류 분석
- 수정 지시 생성

---

## 🔹 Agent Workflow

- LangGraph
- LangChain

### 역할

- Multi-Agent Workflow 구성
- 상태(State) 관리
- Conditional Routing
- Supervisor 기반 흐름 제어

---

## 🔹 Data Processing

- Python
- TypedDict
- JSON Parsing

### 역할

- 리뷰 데이터 처리
- 구조화된 출력 생성
- Batch Processing

---

## 🔹 HITL(Human-in-the-Loop)

### 역할

- 품질 불확실성 보완
- Human 승인 프로세스
- 최종 결과 검수

---

# 📂 프로젝트 구조

```bash
AI-Multi-Agent-Review-System/
│
├── data/
├── outputs/
├── reviews/
│
├── analyzer.py
├── critic.py
├── supervisor.py
├── human_node.py
├── workflow.py
├── app.py
├── utils.py
├── requirements.txt
│
└── README.md
```

---

# 🖥️ 실행 방법

## 1️⃣ 저장소 클론

```bash
git clone https://github.com/your-github-id/AI-Multi-Agent-Review-System.git
```

---

## 2️⃣ 패키지 설치

```bash
pip install -r requirements.txt
```

---

## 3️⃣ API KEY 설정

```python
OPENAI_API_KEY=YOUR_API_KEY
```

---

## 4️⃣ 실행

```bash
python app.py
```

---

# 📸 프로젝트 결과 예시

## 입력

```text
배송은 느렸지만 제품 품질은 좋아요.
```

---

## 출력

```json
{
  "items": [
    {
      "aspect": "배송",
      "label": 0,
      "evidence": "배송은 느렸지만"
    },
    {
      "aspect": "품질",
      "label": 1,
      "evidence": "제품 품질은 좋아요"
    }
  ]
}
```

---

# 💡 프로젝트 특징

## ✅ Multi-Agent 기반 품질 검증 시스템

단순 감성 분석 모델이 아니라:

- 감성 분석
- 품질 검증
- 오류 분석
- Human 승인

까지 포함한 AI Workflow 시스템입니다.

---

## ✅ Supervisor 기반 Orchestration

- Node 기반 Workflow
- 상태(State) 관리
- Agent 흐름 제어
- 정책 기반 Retry

구조를 적용했습니다.

---

## ✅ Human-in-the-Loop(HITL)

AI가 해결하기 어려운 상황에서  
사람이 직접 최종 품질 검수를 수행합니다.

이를 통해:

- 신뢰성 향상
- Hallucination 감소
- 실제 서비스 적용 가능성 강화

를 구현하였습니다.

---

# 📈 기대 효과

## AI 서비스 품질 향상

- 리뷰 분석 자동화
- 품질 검증 자동화
- Human 검수 비용 절감
- 신뢰성 높은 LLM 시스템 구축
- 실제 서비스 적용 가능성 강화

---

# 🧩 향후 개선 방향

- Streamlit 기반 Dashboard 구축
- Vector DB 연동
- RAG 기반 Evidence 검증
- 다국어 리뷰 분석
- 실시간 Human Approval 시스템
- Fine-Tuning 적용
- 관리자 검수 UI 구축

---

# 🎯 프로젝트 핵심 가치

```text
리뷰 데이터를 입력받아
AI가 감성 분석을 수행하고,
Critic 검증과 Human Review까지 자동 처리하는
생성형 AI 기반 Multi-Agent 품질 검증 시스템
```

---

# 👨‍💻 Contributors

- 김남효,박병린,김도훈,이승호,박주영,김민성,강혜원,이채은
- Team Project

---

# 📜 License

This project is licensed under the MIT License.
