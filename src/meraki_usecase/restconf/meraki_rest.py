from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class MerakiRestClient:
    base_url: str
    api_key: str
    timeout_s: int = 30
    max_retries: int = 5

    def __post_init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "X-Cisco-Meraki-API-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

        retry = Retry(
            total=self.max_retries,
            connect=self.max_retries,
            read=self.max_retries,
            status=self.max_retries,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "POST", "PUT", "DELETE", "PATCH"),
            respect_retry_after_header=True,
        )

        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        resp = self.session.get(url, params=params, timeout=self.timeout_s)
        resp.raise_for_status()
        return resp.json()
    
    def get_response(self, path: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        resp = self.session.get(url, params=params, timeout=self.timeout_s)
        resp.raise_for_status()
        return resp


