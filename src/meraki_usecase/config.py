from __future__ import annotations

from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

def _require(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v

@dataclass(frozen=True)
class Settings:
    api_key: str = _require("MERAKI_DASHBOARD_API_KEY")
    org_id: str = _require("MERAKI_ORG_ID")
    network_id: str = _require("MERAKI_NETWORK_ID")
    base_url: str = os.getenv("MERAKI_DASHBOARD_BASE_URL", "https://api.meraki.com/api/v1")
    timeout_s: int = int(os.getenv("MERAKI_REQUEST_TIMEOUT", "30"))
    max_retries: int = int(os.getenv("MERAKI_MAX_RETRIES", "5"))
