# LLM 기반 상품 리뷰 분석 Agent

화장품 리뷰에서 보습·가격·향·포장에 대한 감성과 원문 근거를 추출하고, 분석 결과 검토와 사람의 수정 과정을 연결한 팀 프로젝트입니다.

- 기간: 2026.05.12–2026.05.14
- 팀 구성: 8명
- 김남효 담당: 발표 준비·진행, Multi-Agent 처리 흐름과 HITL·평가 방식 설명

## 문제와 목표

하나의 리뷰에 만족과 불만이 섞여 있으면 긍정·부정 한 가지로 분류하기 어렵습니다. 리뷰를 속성별로 나누고, 각각의 판단 근거를 원문과 연결하는 것을 목표로 했습니다. 화장품 리뷰 분석 상황을 가정한 PoC이며 실제 기업의 운영 실적으로 제시하지 않습니다.

예를 들어 ‘촉촉하지만 가격이 비싸요’는 보습에 대한 긍정과 가격에 대한 부정으로 나눌 수 있습니다.

```json
{"items":[
  {"aspect":"보습","label":1,"evidence":"촉촉하지만"},
  {"aspect":"가격","label":0,"evidence":"가격이 비싸요"}
]}
```

## 팀이 구현한 처리 흐름

1. **Analyzer**: 리뷰에서 속성·감성·근거를 추출합니다.
2. **Critic**: 분석 결과를 검토하고 적합 또는 수정 필요를 판단합니다.
3. **Supervisor**: 오류 유형에 따라 수정 지시를 전달하거나 사람 검토로 전환합니다.
4. **HITL**: 사람이 원문과 결과를 확인하고 항목을 수정·삭제·추가합니다.
5. **배치·대시보드**: 결과를 CSV에 저장하고 Streamlit에서 속성별 감성 분포와 건별 결과를 확인합니다.

LangGraph가 상태와 반복 흐름을 관리합니다. Supervisor는 Critic의 오류 사유를 LLM으로 분류하고, 최종 재시도·종료·HITL 분기는 정책 코드로 결정합니다. 재시도 가능한 유형은 `OUTPUT_ERROR`, `SCOPE_ERROR`, `EVIDENCE_ERROR`이며, `QUALITY_ERROR`·`ETC` 또는 재시도 한도 도달 시 사람 검토로 넘어갑니다.

현재 실행 코드에는 객체 형식·허용 속성·중복·감성 값·원문 근거 검사도 포함되어 있습니다. 단건 검토는 콘솔 입력 방식이며, Streamlit은 결과 조회 화면입니다. 저장 구현은 CSV이며 SQLite 운영 기능으로 설명하지 않습니다.

## 나의 역할

프로젝트 발표를 맡아 기존 리뷰 분석의 한계부터 Agent 처리 흐름, HITL의 필요성, LangSmith 평가와 대시보드까지 이어지도록 발표 내용을 정리했습니다.

각 기능을 따로 나열하기보다 정상 처리, 재시도, 사람 검토로 나뉘는 조건을 중심으로 설명했습니다. 팀원들과 기능별 역할과 State의 데이터 흐름을 확인하며 발표를 준비했고, 분석 결과가 생성된 뒤 검토·저장·조회로 이어지는 과정을 전달했습니다.

## 팀 결과보고서의 성과

| 항목 | Step1 | Step2 | 의미 |
| --- | ---: | ---: | --- |
| format 평가 점수 | 0.64 | 1.00 | 50개 샘플의 출력 형식 규칙 충족 여부 |
| 총 토큰 수 | 93.5K | 65.7K | 보고서에 제시된 두 평가 실행의 사용량 |

`format`은 items 목록, 필수 필드, 감성 값, 속성 중복, Critic 판정 형식을 확인하는 지표입니다. 정답 감성과 비교한 분류 정확도가 아닙니다. 토큰 수는 실제 청구 금액이나 서비스 비용 절감률과 구분합니다. [팀 결과보고서 5쪽](https://drive.google.com/file/d/12zsNLxls7zo_7dN0Lh0NKxm_2IxEjCSR/view)

Streamlit에서는 리뷰 수, 속성별 긍정·부정 비율, 자주 언급된 속성, 건별 분석 결과를 조회했습니다. 하나의 리뷰에 여러 속성이 포함되므로 감성 비율의 분모는 리뷰 수가 아닌 속성별 판정 수입니다.

## 파일과 실행 방법

| 파일 | 용도 |
| --- | --- |
| `Review Analysis System.ipynb` | 기존 작업 노트북. 키 출력과 저장된 실행 출력만 정리 |
| `review_agent.ipynb` | 실행 및 검토에 사용할 노트북 |
| `app.py` | Streamlit 결과 조회 화면 |
| `test_review_agent.py` | API 호출 없이 실행하는 회귀 테스트 |
| `VALIDATION.md` | 코드 수정과 확인 범위 |
| `review-agent-implementation.pdf` | 처리 흐름·역할·판단 기준 요약 |

### 분석 실행

`review_agent.ipynb`를 Colab에서 열고 필요한 환경 설정 및 Agent 정의 셀을 실행합니다. API 키는 환경변수 또는 개인 `api_key.txt`에 설정하며 공개 저장소에 올리지 않습니다.

```text
OPENAI_API_KEY=본인의키
```

- 단건 예제와 배치 실행 셀은 OpenAI API를 호출하므로 선택해서 실행합니다. 전체 셀 반복 실행은 피하세요.
- LangSmith 전송은 기본 비활성화입니다. 평가가 필요할 때 별도 키·데이터셋과 전송 범위를 확인하고 활성화합니다.
- 배치는 `review` 컬럼이 있는 `data.csv`를 입력으로 사용하고, 원본 대신 `review_results.csv`에서 진행합니다. 원본 리뷰 데이터·LangSmith 평가 데이터셋은 저장소에 포함되어 있지 않습니다.
- 사람 검토가 필요한 배치 결과는 `needs_review`로 남습니다. 해당 리뷰를 단건 검토한 뒤 저장하는 별도 처리 과정이 필요합니다.

### 대시보드와 테스트

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

`review_results.csv`가 없으면 준비 안내가 표시됩니다. `demo_results.csv`는 화면 확인용으로 직접 작성한 가상 리뷰 3건이며, 모델 성능이나 실제 고객 데이터를 나타내지 않습니다. API 호출 없이 다음 명령으로 조회할 수 있습니다.

```bash
streamlit run app.py -- --data demo_results.csv
```

```bash
python -m pip install -r requirements-test.txt
python -m pytest test_review_agent.py -q
```

## 한계와 다음 개선

- 허용 속성은 프롬프트에 이미 제시되어 있습니다. 다음 개선은 후보를 새로 정하는 것보다 혼합 감성·무관한 리뷰의 판정 기준과 적용 일관성을 높이는 데 있습니다.
- Critic 검토와 형식 검사는 의미적으로 올바른 감성 판단을 보장하지 않습니다. 정답 라벨 평가와 사람 검토 비율 측정이 필요합니다.
- HITL은 콘솔 방식입니다. 웹 검수 화면과 보류 결과 재개·저장 흐름은 후속 과제입니다.
- 실제 기업 운영, 검수 시간 절감과 고객 만족도 변화는 측정한 성과가 아닙니다.

## 자료

- [팀 결과보고서](https://drive.google.com/file/d/12zsNLxls7zo_7dN0Lh0NKxm_2IxEjCSR/view)
- [구현 설명 PDF](review-agent-implementation.pdf)
- [노션 포트폴리오](https://app.notion.com/p/3617a7a87a17805d8905dae783095310)

팀원: 김남효, 박병린, 김도훈, 이승호, 박주영, 김민성, 강혜원, 이채은

## License

This project is licensed under the MIT License.
