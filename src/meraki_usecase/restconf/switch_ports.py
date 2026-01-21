from __future__ import annotations

from typing import Any, Dict, List, Optional
from meraki_usecase.restconf.meraki_rest import MerakiRestClient

def get_device(client: MerakiRestClient, serial: str) -> Dict[str, Any]:
    return client.get(f"/devices/{serial}")

def get_switch_ports_statuses(
    client: MerakiRestClient,
    serial: str,
    *,
    t0: Optional[str] = None,
    t1: Optional[str] = None,
) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {}
    if t0:
        params["t0"] = t0
    if t1:
        params["t1"] = t1
    return client.get(f"/devices/{serial}/switch/ports/statuses", params=params)
