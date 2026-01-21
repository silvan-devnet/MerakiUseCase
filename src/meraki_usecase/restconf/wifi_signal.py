from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs

from meraki_usecase.restconf.meraki_rest import MerakiRestClient


def _next_link_starting_after(link_header: str) -> Optional[str]:
    """
    Parse RFC5988 Link header and return startingAfter from rel="next" URL if present.
    """
    # Example: <https://api.meraki.com/api/v1/...?...&startingAfter=XYZ>; rel="next"
    parts = [p.strip() for p in link_header.split(",")]
    for part in parts:
        if 'rel="next"' not in part:
            continue
        url_part = part.split(";")[0].strip()
        if url_part.startswith("<") and url_part.endswith(">"):
            url = url_part[1:-1]
            q = parse_qs(urlparse(url).query)
            sa = q.get("startingAfter", [None])[0]
            return sa
    return None


def get_wifi_signal_quality_by_client(
    client: MerakiRestClient,
    org_id: str,
    *,
    timespan: int = 86400,
    network_id: Optional[str] = None,
    serials: Optional[List[str]] = None,
    per_page: int = 1000,
    max_pages: int = 10,
) -> List[Dict[str, Any]]:
    """
    GET /organizations/{organizationId}/wireless/devices/signalQuality/byClient

    Returns list of objects with:
      - snr, rssi
      - client: {id, mac}
      - network: {id, name}
    (beta endpoint; paginated)
    """
    path = f"/organizations/{org_id}/wireless/devices/signalQuality/byClient"

    params: Dict[str, Any] = {"timespan": timespan, "perPage": per_page}
    if network_id:
        params["networkIds[]"] = [network_id]
    if serials:
        params["serials[]"] = serials

    out: List[Dict[str, Any]] = []
    starting_after: Optional[str] = None

    for _ in range(max_pages):
        page_params = dict(params)
        if starting_after:
            page_params["startingAfter"] = starting_after

        resp = client.get_response(path, params=page_params)
        data = resp.json()
        if isinstance(data, list):
            out.extend(data)
        else:
            # Very defensive: if API returns unexpected structure
            break

        link = resp.headers.get("Link", "")
        starting_after = _next_link_starting_after(link) if link else None
        if not starting_after:
            break

    return out
