from __future__ import annotations

from typing import Any, Dict, List
import meraki

def get_switch_health(dashboard: meraki.DashboardAPI, org_id: str, network_id: str) -> List[Dict[str, Any]]:
    return dashboard.organizations.getOrganizationDevicesStatuses(
        org_id,
        networkIds=[network_id],
        productTypes=["switch"],
    )
