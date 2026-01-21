from __future__ import annotations

from typing import Any, Dict, List
import meraki

def get_inventory_devices(dashboard: meraki.DashboardAPI, org_id: str) -> List[Dict[str, Any]]:
    return dashboard.organizations.getOrganizationInventoryDevices(org_id)
