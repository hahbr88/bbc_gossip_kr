import os


def _load_dotenv(path: str = ".env") -> None:
    if not os.path.exists(path):
        return

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_dotenv()

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
GOSSIP_MAIN_URL = "https://www.bbc.com/sport/football/gossip"
ARTICLE_SELECTORS = [
    "div[data-component='text-block'] p[class*='Paragraph']",
    "article p[class*='Paragraph']",
    "main p[class*='Paragraph']",
    "p[class*='Paragraph']",
]

DRY_RUN = os.getenv("DRY_RUN") == "1"

def get_slack_webhook_url() -> str:
    url = os.getenv("SLACK_WEBHOOK_URL")
    if not url:
        raise ValueError("SLACK_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")
    return url
