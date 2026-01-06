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
