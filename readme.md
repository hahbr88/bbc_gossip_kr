# ⚽ BBC Football Gossip Translator KR

[![BBC Gossip KR Daily](https://github.com/hahbr88/bbc_gossip_kr/actions/workflows/bbc_gossip.yml/badge.svg)](https://github.com/hahbr88/bbc_gossip_kr/actions/workflows/bbc_gossip.yml)

BBC Football Gossip 기사를 자동으로 수집하여  
👉 **한국어로 번역 후 Slack으로 전송하는 봇**입니다.

Ubuntu VM cron 기반으로  
**매일 KST 오전 10시에 실행**되도록 구성했습니다.

GitHub Actions는 정기 스케줄을 비활성화하고, 필요할 때 수동 실행만 가능하도록 유지합니다.

---

## 📌 주요 기능

- BBC Football Gossip 최신 기사 자동 수집
- 기사 본문 가십 문단 추출 및 정제
- 영어 → 한국어 자동 번역
- 가십 문장 끝의 출처 정보 (Mirror, Fabrizio Romano 등)는 원문 그대로 유지
- 출처 정보에 원문 기사 링크 삽입
- BBC HTML 구조 변경 대비 fallback selector 적용
- 실제 BBC 페이지 기반 smoke test로 파싱 가능 여부 검증
- 파싱 실패 시 성공 처리하지 않고 진단 로그와 함께 실패 처리
- Slack Webhook을 통해 메시지 전송
- Ubuntu VM cron을 통한 매일 KST 10:00 스케줄 실행
- GitHub Actions 수동 실행 지원

---

## 🧩 기술스택

#### Backend

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)

#### CI/CD

![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![Cron](https://img.shields.io/badge/Cron-222222?style=for-the-badge&logo=linux&logoColor=white)

### Integration

![Slack Webhook](https://img.shields.io/badge/Slack%20Webhook-4A154B?style=for-the-badge&logo=slack&logoColor=white)

### Crawling & Translation

![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-59666C?style=for-the-badge&logo=python&logoColor=white)
![Requests](https://img.shields.io/badge/Requests-20232A?style=for-the-badge&logo=python&logoColor=white)
![deep-translator](https://img.shields.io/badge/deep--translator-0A0A0A?style=for-the-badge&logo=googletranslate&logoColor=white)

___

## 🏗️ 아키텍처

```text
Ubuntu VM cron (매일 10:00 KST)
        │
        ▼
python app.py
        │
        ▼
pipeline.run()
  ├─ config.get_slack_webhook_url()
  ├─ bbc_parse.get_latest_gossip_url()
  ├─ bbc_parse.parse_gossip_article(url)
  ├─ bbc_parse.select_article_paragraphs(soup)
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
├─ tests/
│  ├─ test_bbc_parse.py
│  └─ test_bbc_smoke.py
└─ .github/
   └─ workflows/
      └─ bbc_gossip.yml

```

---

## 🚀 실행 환경

- Ubuntu VM
- Python 3.10+ (VM), Python 3.12 (GitHub Actions 수동 실행)
- cron
- Slack Incoming Webhook

---

## 🟢 Ubuntu VM cron 실행 방식

- Ubuntu VM에서 매일 KST 오전 10시에 실행
- `flock`으로 중복 실행 방지
- 실행 로그는 `logs/cron.log`에 저장
- VM 기준 권장 스펙: RAM 1GB, CPU 1 core, swap 유지

현재 cron 설정 예시:

```cron
0 10 * * * cd /home/bbcbot/projects/bbc_gossip_kr && flock -n /tmp/bbc_gossip_kr.lock .venv/bin/python app.py >> logs/cron.log 2>&1
```

cron 등록 확인:

```bash
crontab -l
```

로그 확인:

```bash
tail -n 100 /home/bbcbot/projects/bbc_gossip_kr/logs/cron.log
```

> 로컬 PC 위에서 실행되는 VM의 경우, 호스트가 sleep 상태에 들어가면 cron도 실행되지 않습니다. 상시 운영하려면 VM이 실행 중이고 호스트도 깨어 있어야 합니다.

## 🟢 GitHub Actions 실행 방식

- 정기 schedule은 비활성화
- `workflow_dispatch`를 통한 수동 실행만 지원
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

### DRY_RUN 실행

Slack 실제 전송 없이 전체 수집/파싱/번역 흐름을 확인하려면 `DRY_RUN=1`로 실행합니다.

```bash
DRY_RUN=1 python app.py
```

정상 실행 시 마지막에 아래와 비슷한 결과가 출력됩니다.

```text
{'statusCode': 200, 'body': 'Gossip N개'}
```

실제 Slack으로 전송하려면 `SLACK_WEBHOOK_URL`을 설정하고 `DRY_RUN`을 제거하거나 `DRY_RUN=0`으로 실행합니다.

```bash
python app.py
```

### 테스트 실행

샘플 HTML 기반 파서 테스트를 실행합니다.

```bash
python -m unittest tests.test_bbc_parse
```

실제 BBC 페이지를 가져와 현재 HTML 구조와 파서가 맞는지 smoke test를 실행합니다.

```bash
SMOKE_TEST=1 python -m unittest tests.test_bbc_smoke
```

일반 test discovery에서는 smoke test가 자동으로 skip됩니다.

```bash
python -m unittest discover -s tests
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
- BBC 기사 본문 selector를 단일 값이 아닌 fallback selector 목록으로 관리
- 출처 없는 요약/캡션/저작권 문단은 가십 항목에서 제외
- BBC 내부 팀 링크를 출처 링크로 오인하지 않도록 필터링
- 최신 기사에서 가십 항목을 0개 추출하면 파싱 실패로 처리
- 정상 실행 로그에 기사 URL, 제목, 발행일, 선택 selector, 문단 수, 추출 개수 출력
- DRY_RUN 모드를 도입하여 로컬 테스트 시 Slack 실제 전송 방지
- Ubuntu VM cron으로 매일 KST 10:00 실행
- GitHub Actions는 수동 실행 용도로 유지

## 🧯 트러블슈팅

- GitHub Actions와 VM cron 중복 발송 문제
  - 원인: GitHub Actions schedule과 VM cron이 동시에 활성화되면 같은 날 Slack 메시지가 중복 발송될 수 있음
  - 해결: VM cron 마이그레이션 후 GitHub Actions schedule 제거, 수동 실행만 유지
- BBC HTML 구조 변경으로 가십 문단을 0개 추출하는 문제
  - 원인: 기존 selector `div[data-component='text-block'] p[class*='Paragraph']`가 현재 BBC 상세 페이지 구조와 맞지 않음
  - 결과: 실제로는 파싱이 깨졌지만 `가십 없음`으로 정상 종료됨
  - 해결: fallback selector 목록을 도입하고, 실제 BBC 페이지 smoke test와 파싱 진단 로그 추가
- BBC 본문 특수문자 깨짐 문제
  - 원인: 응답 charset이 명확하지 않아 `requests`가 `ISO-8859-1`로 오판
  - 결과: `£`, `€`, `–` 같은 문자가 깨질 수 있음
  - 해결: `apparent_encoding` 기반으로 응답 인코딩 보정
- 이슈 마커가 오늘 실행된 것으로 잘못 인식되는 문제
  - 원인: `jq`에서 `env.DAY`를 사용했지만 해당 환경 변수가 설정되지 않아 `test("KST=")`로 동작
  - 결과: 과거 코멘트도 매칭되어 매일 이미 실행된 것으로 판단
  - 해결: 쉘 변수 `DAY`를 문자열에 직접 삽입해 `test("KST=YYYY-MM-DD")`로 정확히 매칭

## 🔮 향후 개선 계획

- ~~EventBridge 스케줄을 통한 정기 자동 실행~~
- ~~Ubuntu VM cron job 기반 실행으로 마이그레이션~~
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
