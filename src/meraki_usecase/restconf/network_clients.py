from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qs

from meraki_usecase.restconf.meraki_rest import MerakiRestClient


def _next_link_starting_after(link_header: str) -> Optional[str]:
    # <...&startingAfter=XYZ>; rel="next"
    parts = [p.strip() for p in link_header.split(",")]
    for part in parts:
        if 'rel="next"' not in part:
            continue
        url_part = part.split(";")[0].strip()
        if url_part.startswith("<") and url_part.endswith(">"):
            url = url_part[1:-1]
            q = parse_qs(urlparse(url).query)
            return q.get("startingAfter", [None])[0]
    return None


def get_network_clients(
    client: MerakiRestClient,
    network_id: str,
    *,
    timespan: int = 86400,
    per_page: int = 1000,
    max_pages: int = 20,
    connection_types: Optional[List[str]] = None,  # ["Wired","Wireless"]
) -> List[Dict[str, Any]]:
    """
    GET /networks/{networkId}/clients
    Returns clients in the timespan. Includes usage.sent/recv. (usage is in KB)
    """
    path = f"/networks/{network_id}/clients"
    base_params: Dict[str, Any] = {"timespan": timespan, "perPage": per_page}

    if connection_types:
        base_params["recentDeviceConnections[]"] = connection_types

    out: List[Dict[str, Any]] = []
    starting_after: Optional[str] = None

    for _ in range(max_pages):
        params = dict(base_params)
        if starting_after:
            params["startingAfter"] = starting_after

        resp = client.get_response(path, params=params)
        data = resp.json()
        if isinstance(data, list):
            out.extend(data)
        else:
            break

        link = resp.headers.get("Link", "")
        starting_after = _next_link_starting_after(link) if link else None
        if not starting_after:
            break

    return out
