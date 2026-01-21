from __future__ import annotations

from typing import Any, Dict, List, Optional

from meraki_usecase.config import Settings

# REST mode pieces
from meraki_usecase.restconf.meraki_rest import MerakiRestClient
from meraki_usecase.restconf.orgs import org_id_to_name_map as rest_org_id_to_name_map
from meraki_usecase.restconf.inventory import get_inventory_devices as rest_inventory
from meraki_usecase.restconf.health import get_switch_health as rest_switch_health
from meraki_usecase.restconf.health_ap import get_ap_health as rest_ap_health
from meraki_usecase.restconf.switch_ports import get_switch_ports_statuses as rest_switch_ports

# SDK mode pieces
from meraki_usecase.sdk.meraki_sdk import build_dashboard
from meraki_usecase.sdk.orgs import org_id_to_name_map as sdk_org_id_to_name_map
from meraki_usecase.sdk.inventory import get_inventory_devices as sdk_inventory
from meraki_usecase.sdk.health import get_switch_health as sdk_switch_health
from meraki_usecase.sdk.health_ap import get_ap_health as sdk_ap_health
from meraki_usecase.sdk.switch_ports import get_switch_ports_statuses as sdk_switch_ports


def _s(v: Any) -> str:
    return "" if v is None else str(v)

def _cut(s: str, n: int) -> str:
    s = s.replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"

def _row(values: List[Any], widths: List[int]) -> str:
    return " | ".join(_cut(_s(v), w).ljust(w) for v, w in zip(values, widths))

def print_table(headers: List[str], rows: List[List[Any]], widths: List[int]) -> None:
    print(_row(headers, widths))
    print("-+-".join("-" * w for w in widths))
    for r in rows:
        print(_row(r, widths))


def _get_first(d: dict, path: list, default=""):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def _join_list(v):
    if isinstance(v, list):
        return ",".join(str(x) for x in v)
    return ""


# ---------------------------
# Resolving names
# ---------------------------

def resolve_org_name_rest(client: MerakiRestClient, org_id: str) -> str:
    m = rest_org_id_to_name_map(client)
    return m.get(org_id, "")

def resolve_org_name_sdk(dashboard, org_id: str) -> str:
    m = sdk_org_id_to_name_map(dashboard)
    return m.get(org_id, "")

def resolve_network_name_rest(client: MerakiRestClient, network_id: str) -> str:
    # GET /networks/{networkId}
    try:
        net = client.get(f"/networks/{network_id}")
        return _s(net.get("name", ""))
    except Exception:
        return ""

def resolve_network_name_sdk(dashboard, network_id: str) -> str:
    # SDK: networks.getNetwork(networkId)
    try:
        net = dashboard.networks.getNetwork(network_id)
        return _s(net.get("name", ""))
    except Exception:
        return ""


# ---------------------------
# Menu actions
# ---------------------------

def action_inventory(mode: str, client, dashboard, settings: Settings) -> None:
    limit = int(input("Limit (default 50): ") or "50")
    if mode == "rest":
        devs = rest_inventory(client, settings.org_id)[:limit]
    else:
        devs = sdk_inventory(dashboard, settings.org_id)[:limit]

    rows = [[d.get("serial"), d.get("model"), d.get("networkId"), d.get("claimedAt")] for d in devs]
    print_table(["Serial", "Model", "Network ID", "Claimed At"], rows, [16, 10, 22, 25])

def action_switch_health(mode: str, client, dashboard, settings: Settings, network_id: str) -> None:
    limit = int(input("Limit (default 50): ") or "50")
    if mode == "rest":
        devs = rest_switch_health(client, settings.org_id, network_id)[:limit]
    else:
        devs = sdk_switch_health(dashboard, settings.org_id, network_id)[:limit]

    rows = [[d.get("name"), d.get("serial"), d.get("model"), d.get("status"), d.get("lastReportedAt")] for d in devs]
    print_table(["Name", "Serial", "Model", "Status", "Last Reported"], rows, [28, 16, 10, 10, 25])

def action_ap_health(mode: str, client, dashboard, settings: Settings, network_id: str) -> None:
    limit = int(input("Limit (default 50): ") or "50")
    if mode == "rest":
        devs = rest_ap_health(client, settings.org_id, network_id)[:limit]
    else:
        devs = sdk_ap_health(dashboard, settings.org_id, network_id)[:limit]

    rows = [[d.get("name"), d.get("serial"), d.get("model"), d.get("status"), d.get("lastReportedAt")] for d in devs]
    print_table(["Name", "Serial", "Model", "Status", "Last Reported"], rows, [28, 16, 10, 10, 25])

def action_switch_ports(mode: str, client, dashboard, settings: Settings, network_id: str) -> None:
    choice = input("1) Single switch by serial  2) All switches in network  (default 2): ") or "2"
    limit = int(input("Max rows (default 200): ") or "200")

    switches: List[Dict[str, Any]] = []
    if choice.strip() == "1":
        serial = input("Enter switch serial (e.g. Q2XX-...): ").strip()
        if not serial:
            print("No serial provided.")
            return
        # We can keep name blank (or you can add getDevice lookup later)
        switches = [{"serial": serial, "name": ""}]
    else:
        # Use switch health list as our switch list (name + serial)
        if mode == "rest":
            switches = rest_switch_health(client, settings.org_id, network_id)
        else:
            switches = sdk_switch_health(dashboard, settings.org_id, network_id)
        switches = [s for s in switches if s.get("serial")]

    rows: List[List[Any]] = []
    for sw in switches:
        serial = sw.get("serial")
        sw_name = sw.get("name", "")

        if mode == "rest":
            ports = rest_switch_ports(client, serial)
        else:
            ports = sdk_switch_ports(dashboard, serial)

        for p in ports:
            rows.append([
                sw_name,
                serial,
                p.get("portId"),
                p.get("status"),
                p.get("isUplink"),
                p.get("speed"),
                p.get("duplex"),
                _get_first(p, ["poe", "isAllocated"], ""),
                p.get("clientCount", ""),
                _join_list(_get_first(p, ["spanningTree", "statuses"], [])),
                len(p.get("errors", []) or []),
                len(p.get("warnings", []) or []),
            ])

            if len(rows) >= limit:
                break
        if len(rows) >= limit:
            break

    print_table(
        ["Switch", "Serial", "Port", "Status", "Uplink", "Speed", "Duplex", "PoE", "Clients", "STP", "Errors", "Warnings"],
        rows,
        [22, 16, 5, 12, 6, 10, 6, 5, 7, 12, 6, 8],
    )


# ---------------------------
# Main interactive menu
# ---------------------------

def main() -> None:
    settings = Settings()

    mode = (input("Choose mode: 1 REST  2 SDK  (default 1): ").strip() or "1")
    mode = "sdk" if mode == "2" else "rest"

    client = None
    dashboard = None

    if mode == "rest":
        client = MerakiRestClient(
            base_url=settings.base_url,
            api_key=settings.api_key,
            timeout_s=settings.timeout_s,
            max_retries=settings.max_retries,
        )
        org_name = resolve_org_name_rest(client, settings.org_id)
        net_name = resolve_network_name_rest(client, settings.network_id)
    else:
        dashboard = build_dashboard(settings)
        org_name = resolve_org_name_sdk(dashboard, settings.org_id)
        net_name = resolve_network_name_sdk(dashboard, settings.network_id)

    print("\n--- Current selection (from .env) ---")
    print(f"Mode      : {mode}")
    print(f"Org ID    : {settings.org_id}")
    print(f"Org Name  : {org_name or '(not resolved)'}")
    print(f"Network ID: {settings.network_id}")
    print(f"Net Name  : {net_name or '(not resolved)'}")
    print("------------------------------------\n")

    while True:
        print("Menu")
        print(" 1) Inventory (org)")
        print(" 2) Switch health (network)")
        print(" 3) AP health (network)")
        print(" 4) Switch ports (serial or all)")
        print(" 0) Exit")
        choice = input("Select (0-4): ").strip()

        if choice == "0":
            print("Bye.")
            return

        try:
            if choice == "1":
                action_inventory(mode, client, dashboard, settings)
            elif choice == "2":
                action_switch_health(mode, client, dashboard, settings, settings.network_id)
            elif choice == "3":
                action_ap_health(mode, client, dashboard, settings, settings.network_id)
            elif choice == "4":
                action_switch_ports(mode, client, dashboard, settings, settings.network_id)
            else:
                print("Unknown option.\n")
        except Exception as e:
            print(f"\nERROR: {e}\n")


if __name__ == "__main__":
    main()