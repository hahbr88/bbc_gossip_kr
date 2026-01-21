# ⚽ BBC Football Gossip Translator KR (AWS Lambda)

BBC Football Gossip 기사를 자동으로 수집하여  
👉 **한국어로 번역 후 Slack으로 전송하는 봇**입니다.

GitHub Actions 기반으로  
**매일 KST 기준 스케줄/수동 실행**되도록 구성했습니다.


---

## 📌 주요 기능

- BBC Football Gossip 최신 기사 자동 수집
- 기사 본문 가십 문단 추출 및 정제
- 영어 → 한국어 자동 번역
- 가십 문장 끝의 출처 정보 (Mirror, Fabrizio Romano 등)는 원문 그대로 유지
- 출처 정보에 원문 기사 링크 삽입
- Slack Webhook을 통해 메시지 전송
- AWS Lambda 기반 서버리스 실행
- GitHub Actions를 통한 CI/CD 자동 배포

---
## 🧩 기술스택

#### Backend
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)


#### CI/CD
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)

### Integration
![Slack Webhook](https://img.shields.io/badge/Slack%20Webhook-4A154B?style=for-the-badge&logo=slack&logoColor=white)

### Crawling & Translation
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-59666C?style=for-the-badge&logo=python&logoColor=white)
![Requests](https://img.shields.io/badge/Requests-20232A?style=for-the-badge&logo=python&logoColor=white)
![deep-translator](https://img.shields.io/badge/deep--translator-0A0A0A?style=for-the-badge&logo=googletranslate&logoColor=white)

___

## 🏗️ 아키텍처

```text
GitHub Actions (cron / 수동 실행)
        │
        ▼
python app.py
        │
        ▼
pipeline.run()
  ├─ config.get_slack_webhook_url()
  ├─ bbc_parse.get_latest_gossip_url()
  ├─ bbc_parse.parse_gossip_article(url)
  ├─ bbc_parse.extract_gossip_items(soup)
  ├─ bbc_translate.preprocess_translate(items)
  ├─ bbc_translate.google_translator(refined_with_tokens, tails)
  └─ pipeline.send_slack_message(message, webhook_url)
        │
        ▼
Slack Incoming Webhook
```
---

## 📂 프로젝트 구조
```
bbc_gossip_kr/
├─ app.py
├─ pipeline.py
├─ config.py
├─ bbc_http.py
├─ bbc_parse.py
├─ bbc_translate.py
├─ requirements.txt
├─ Dockerfile
├─ readme.md
└─ .github/
   └─ workflows/
      └─ bbc_gossip.yml

```
---

## 🚀 실행 환경
- Python 3.12 (GitHub Actions)
- GitHub Actions
- Slack Incoming Webhook
---

## 🟢 GitHub Actions 실행 방식
- 매일 KST 기준으로 스케줄 실행
- 동일 날짜(KST)에는 캐시/이슈 마커로 중복 실행 방지
- 수동 실행 시 `force_run=true`로 마커를 무시하고 강제 실행 가능


## 🟡 로컬환경 테스트
```bash
# 가상환경 생성 및 활성화 (최초 1회)

# macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\activate
```
```bash
# 의존성 설치
pip install -r requirements.txt
```
```bash
# 환경변수 설정 (1회성)
# macOS / Linux
export SLACK_WEBHOOK_URL="여기에_슬랙_웹훅_URL"
export DRY_RUN=1

# Windows PowerShell
setx SLACK_WEBHOOK_URL "여기에_슬랙_웹훅_URL"
setx DRY_RUN "1"
 
# DRY_RUN 로컬 테스트 시 Slack 실제 전송 방지, 1이 아니거나 none이면 슬랙 전송됨

```
```md
※ 또는 프로젝트 루트에 `.env` 파일을 만들어 아래처럼 설정할 수 있습니다.
SLACK_WEBHOOK_URL=...
DRY_RUN=1
```

```bash
# 실행
python app.py
```
## 🐳 Docker 환경 구축하기
1) 이미지 빌드
```bash
docker build -t bbc-gossip:latest .
```
2) 실행 (env 파일 사용)
```bash
docker run --rm --env-file .env bbc-gossip:latest
```



## 🛠️ 문제 해결 & 설계 포인트

- 번역 API 다중 호출로 인한 지연 문제를 단일 배치 번역 구조로 리팩터링
- 가십 문장 끝의 출처 정보는 번역하지 않고 원문 유지하도록 토큰 기반 처리
- DRY_RUN 모드를 도입하여 로컬 테스트 시 Slack 실제 전송 방지
- Github Action으로 특정 시간 코드 실행


## 🔮 향후 개선 계획

- ~~EventBridge 스케줄을 통한 정기 자동 실행~~
- 번역 엔진 교체 또는 다중 번역기 fallback 구조
- Slack 메시지 길이 제한 대응(자동 분할 전송)

## 📚 과거 구성 (히스토리)
- AWS Lambda + GitHub Actions 기반 자동 배포 파이프라인
  - GitHub Actions 배포 흐름
    1. main 브랜치에 push
    2. GitHub Actions 자동 실행
    3. Python 의존성 설치
    4. Lambda 배포용 zip 생성
    5. 배포 파일 검증 (app.py, lambda_function.py 포함 여부)
    6. aws lambda update-function-code 실행
    7. Lambda 스모크 테스트(1회 invoke)로 정상 동작 여부 확인

- ![AWS Lambda](https://img.shields.io/badge/AWS%20Lambda-FF9900?style=for-the-badge&logo=awslambda&logoColor=white) ![AWS IAM](https://img.shields.io/badge/AWS%20IAM-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white)


## 📄 License
This project is for educational and personal use only.
