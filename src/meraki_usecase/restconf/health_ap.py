from __future__ import annotations

from typing import Any, Dict, List
from meraki_usecase.restconf.meraki_rest import MerakiRestClient

def get_ap_health(client: MerakiRestClient, org_id: str, network_id: str) -> List[Dict[str, Any]]:
    # GET /organizations/{orgId}/devices/statuses?networkIds[]=...&productTypes[]=wireless
    params = {
        "networkIds[]": [network_id],
        "productTypes[]": ["wireless"],
    }
    return client.get(f"/organizations/{org_id}/devices/statuses", params=params)
