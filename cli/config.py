import os
from pathlib import Path
from dotenv import load_dotenv

_root = Path(__file__).parent.parent

# 加载顺序：~/.elc/.env（全局）→ 工程目录 .env.local → .env
# 后加载的优先级更高，工程级配置可覆盖全局配置
load_dotenv(Path.home() / ".elc" / ".env")
load_dotenv(_root / ".env.local")
load_dotenv(_root / ".env")

BASE_URL: str = os.getenv("BASE_URL", "http://localhost:12007/xm-demo").rstrip("/")
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))

SSO_CONFIG: dict = {
    "app_id":      os.getenv("SSO_APP_ID", "sso"),
    "secret":      os.getenv("SSO_SECRET", ""),
    "domain":      os.getenv("SSO_DOMAIN", "kingdee-fpy"),
    "mobile":      os.getenv("SSO_MOBILE", ""),
    "username":    os.getenv("SSO_USERNAME", ""),
    "work_number": os.getenv("SSO_WORK_NUMBER", ""),
    "org_num":     os.getenv("SSO_ORG_NUM", ""),
}

DEFAULT_HEADERS: dict = {
    "Content-Type":   "application/json",
    "Accept-Language": "zh-CN",
    "Authorization":  "",
    "X-Company-ID":   os.getenv("X_COMPANY_ID", ""),
}
