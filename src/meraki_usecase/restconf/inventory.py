from __future__ import annotations

from typing import Any, Dict, List
from meraki_usecase.restconf.meraki_rest import MerakiRestClient

def get_inventory_devices(client: MerakiRestClient, org_id: str) -> List[Dict[str, Any]]:
    # GET /organizations/{orgId}/inventoryDevices
    return client.get(f"/organizations/{org_id}/inventoryDevices")
