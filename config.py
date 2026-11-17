import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _parse_admin_ids(value: str) -> list[int]:
    ids = []
    for part in value.split(","):
        part = part.strip()
        if part:
            try:
                ids.append(int(part))
            except ValueError:
                pass
    return ids


def _resolve_webapp_url() -> str:
    # Render o'z domenini RENDER_EXTERNAL_HOSTNAME orqali beradi — eng ishonchli manba.
    render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
    if render_host:
        return f"https://{render_host}"
    return os.getenv("WEBAPP_URL", "http://localhost:8000")


@dataclass
class Config:
    customer_bot_token: str = os.getenv("CUSTOMER_BOT_TOKEN", "")
    admin_bot_token: str = os.getenv("ADMIN_BOT_TOKEN", "")
    admin_ids: list[int] = None
    webapp_url: str = None
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    database_path: str = os.getenv("DATABASE_PATH", "hotdog_mafia.db")

    def __post_init__(self):
        if self.admin_ids is None:
            self.admin_ids = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
        if self.webapp_url is None:
            self.webapp_url = _resolve_webapp_url()


config = Config()
