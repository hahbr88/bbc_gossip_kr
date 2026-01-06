# ⚽ BBC Football Gossip Translator KR (AWS Lambda)

BBC Football Gossip 기사를 자동으로 수집하여  
👉 **한국어로 번역 후 Slack으로 전송하는 서버리스 봇**입니다.

AWS Lambda + GitHub Actions 기반으로  
**서버 관리 없이 자동 배포 / 자동 실행**되도록 구성했습니다.

---

## 📌 주요 기능

- BBC Football Gossip 최신 기사 자동 수집
- 기사 본문 가십 문단 추출 및 정제
- 영어 → 한국어 자동 번역
- Slack Webhook을 통해 메시지 전송
- AWS Lambda 기반 서버리스 실행
- GitHub Actions를 통한 CI/CD 자동 배포

---
## 🧩 기술스택

#### Backend
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![AWS Lambda](https://img.shields.io/badge/AWS%20Lambda-FF9900?style=for-the-badge&logo=awslambda&logoColor=white)
![AWS IAM](https://img.shields.io/badge/AWS%20IAM-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white)


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
GitHub (push)
   ↓
GitHub Actions (CI/CD)
   ↓
AWS Lambda
   ↓
BBC 사이트 크롤링
   ↓
번역
   ↓
Slack 전송
```
---

## 📂 프로젝트 구조
```
bbc-gossip-lambda/
├─ lambda_function.py        # Lambda 메인 함수
├─ requirements.txt          # Python 의존성
├─ README.md
└─ .github/
   └─ workflows/
      └─ deploy.yml          # GitHub Actions 배포 설정

```
---

## 🚀 실행 환경
- Python 3.11
- AWS Lambda (python3.11 runtime)
- GitHub Actions
- Slack Incoming Webhook
---

## ⚙️ GitHub Actions 배포 흐름
1. main 브랜치에 push
2. GitHub Actions 자동 실행
3. Python 의존성 설치
4. Lambda 배포용 zip 생성
5. aws lambda update-function-code 실행
6. Lambda 함수 업데이트 완료


## 🧪 수동 실행 (CLI)
```bash
# 실행
aws lambda invoke \
  --function-name bbc-gossip \
  response.json

# 로그확인
aws logs tail /aws/lambda/bbc-gossip --follow
```



## 📄 License
This project is for educational and personal use only.