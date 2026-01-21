from __future__ import annotations

from typing import Any, Dict, List, Optional
import inspect
import meraki


def _call_session_get(dashboard: meraki.DashboardAPI, path: str, params: Dict[str, Any]) -> Any:
    session = getattr(dashboard, "_session", None)
    if session is None:
        raise RuntimeError("DashboardAPI has no _session; cannot perform raw GET fallback.")

    get_fn = getattr(session, "get", None)
    if get_fn is None:
        raise RuntimeError("DashboardAPI._session has no get() method; cannot perform raw GET fallback.")

    metadata = {"tags": ["networks", "clients", "monitor"], "operation": "getNetworkClients"}
    sig = inspect.signature(get_fn)
    n_params = len(sig.parameters)

    if n_params >= 3:
        return get_fn(metadata, path, params)
    return get_fn(path, params)


def get_network_clients(
    dashboard: meraki.DashboardAPI,
    network_id: str,
    *,
    timespan: int = 86400,
    per_page: int = 1000,
    connection_types: Optional[List[str]] = None,  # ["Wired","Wireless"]
) -> List[Dict[str, Any]]:
    """
    SDK first, fallback to raw GET via RestSession.
    """
    # Preferred: SDK method
    method = getattr(dashboard.networks, "getNetworkClients", None)
    if callable(method):
        kwargs: Dict[str, Any] = {"timespan": timespan, "perPage": per_page}

        if connection_types:
            kwargs["recentDeviceConnections"] = connection_types

        # SDK supports pagination helper pattern
        try:
            return method(network_id, total_pages="all", **kwargs)
        except TypeError:
            # Some versions may not accept total_pages
            return method(network_id, **kwargs)

    # Fallback: raw GET
    params: Dict[str, Any] = {"timespan": timespan, "perPage": per_page}
    if connection_types:
        params["recentDeviceConnections[]"] = connection_types

    path = f"/networks/{network_id}/clients"
    data = _call_session_get(dashboard, path, params)

    return data if isinstance(data, list) else []
