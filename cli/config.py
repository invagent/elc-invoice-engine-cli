import os
from pathlib import Path
from dotenv import load_dotenv

# 从工程根目录的 .env.local → .env 依次加载
_root = Path(__file__).parent.parent
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
