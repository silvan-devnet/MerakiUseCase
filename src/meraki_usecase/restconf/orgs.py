from __future__ import annotations

from typing import Dict, List, Any
from meraki_usecase.restconf.meraki_rest import MerakiRestClient

def get_organizations(client: MerakiRestClient) -> List[Dict[str, Any]]:
    return client.get("/organizations")

def org_name_to_id_map(client: MerakiRestClient) -> Dict[str, str]:
    orgs = get_organizations(client)
    return {o["name"]: o["id"] for o in orgs}

def org_id_to_name_map(client: MerakiRestClient) -> Dict[str, str]:
    orgs = get_organizations(client)
    return {o["id"]: o["name"] for o in orgs}
