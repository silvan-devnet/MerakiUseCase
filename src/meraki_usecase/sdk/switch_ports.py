from __future__ import annotations

from typing import Any, Dict, List, Optional
import meraki

def get_device(dashboard: meraki.DashboardAPI, serial: str) -> Dict[str, Any]:
    return dashboard.devices.getDevice(serial)

def get_switch_ports_statuses(
    dashboard: meraki.DashboardAPI,
    serial: str,
    *,
    t0: Optional[str] = None,
    t1: Optional[str] = None,
) -> List[Dict[str, Any]]:
    kwargs = {}
    if t0:
        kwargs["t0"] = t0
    if t1:
        kwargs["t1"] = t1
    return dashboard.switch.getDeviceSwitchPortsStatuses(serial, **kwargs)
