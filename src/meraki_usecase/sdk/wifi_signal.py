from __future__ import annotations

from typing import Any, Dict, List, Optional
import inspect
import meraki


def _call_session_get(dashboard: meraki.DashboardAPI, path: str, params: Dict[str, Any]) -> Any:
    """
    Call the Meraki SDK's internal RestSession.get() in a version-tolerant way.
    Some SDK versions use: get(url, params)
    Others use: get(metadata, url, params)
    """
    session = getattr(dashboard, "_session", None)
    if session is None:
        raise RuntimeError("DashboardAPI has no _session; cannot perform raw GET fallback.")

    get_fn = getattr(session, "get", None)
    if get_fn is None:
        raise RuntimeError("DashboardAPI._session has no get() method; cannot perform raw GET fallback.")

    metadata = {
        "tags": ["wireless", "devices", "monitor"],
        "operation": "getOrganizationWirelessDevicesSignalQualityByClient",
    }

    sig = inspect.signature(get_fn)
    n_params = len(sig.parameters)

    # Bound method: signatures typically appear as (url, params=None) or (metadata, url, params=None)
    if n_params >= 3:
        return get_fn(metadata, path, params)
    return get_fn(path, params)


def get_wifi_signal_quality_by_client(
    dashboard: meraki.DashboardAPI,
    org_id: str,
    *,
    timespan: int = 86400,
    network_id: Optional[str] = None,
    serials: Optional[List[str]] = None,
    per_page: int = 1000,
) -> List[Dict[str, Any]]:
    """
    Endpoint (beta): GET /organizations/{organizationId}/wireless/devices/signalQuality/byClient

    Returns list entries like:
      - snr, rssi
      - client: {id, mac}
      - network: {id, name}
    """
    # Prefer generated SDK method when available
    orgs = dashboard.organizations
    method = getattr(orgs, "getOrganizationWirelessDevicesSignalQualityByClient", None)
    if callable(method):
        kwargs: Dict[str, Any] = {"timespan": timespan, "perPage": per_page}
        if network_id:
            kwargs["networkIds"] = [network_id]   # generated method usually handles this correctly
        if serials:
            kwargs["serials"] = serials
        return method(org_id, **kwargs)

    # Fallback: raw GET via SDK session.
    # IMPORTANT: pass array params using the "[]"-style keys so the API sees arrays.
    # This avoids the 400 "'networkIds' must be an array".
    params: Dict[str, Any] = {"timespan": timespan, "perPage": per_page}
    if network_id:
        params["networkIds[]"] = [network_id]
    if serials:
        params["serials[]"] = serials

    path = f"/organizations/{org_id}/wireless/devices/signalQuality/byClient"
    data = _call_session_get(dashboard, path, params)

    return data if isinstance(data, list) else []
