from __future__ import annotations

from typing import Dict
import meraki

def org_name_to_id_map(dashboard: meraki.DashboardAPI) -> Dict[str, str]:
    orgs = dashboard.organizations.getOrganizations()
    return {o["name"]: o["id"] for o in orgs}

def org_id_to_name_map(dashboard: meraki.DashboardAPI) -> Dict[str, str]:
    orgs = dashboard.organizations.getOrganizations()
    return {o["id"]: o["name"] for o in orgs}
