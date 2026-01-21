from __future__ import annotations

import argparse
from typing import Any, List

from meraki_usecase.config import Settings

from meraki_usecase.restconf.meraki_rest import MerakiRestClient
from meraki_usecase.restconf.orgs import org_name_to_id_map as rest_org_map
from meraki_usecase.restconf.inventory import get_inventory_devices as rest_inventory
from meraki_usecase.restconf.health import get_switch_health as rest_switch_health

from meraki_usecase.sdk.meraki_sdk import build_dashboard
from meraki_usecase.sdk.orgs import org_name_to_id_map as sdk_org_map
from meraki_usecase.sdk.inventory import get_inventory_devices as sdk_inventory
from meraki_usecase.sdk.health import get_switch_health as sdk_switch_health
from meraki_usecase.restconf.health_ap import get_ap_health as rest_ap_health
from meraki_usecase.sdk.health_ap import get_ap_health as sdk_ap_health
from meraki_usecase.restconf.switch_ports import get_switch_ports_statuses as rest_switch_ports
from meraki_usecase.sdk.switch_ports import get_switch_ports_statuses as sdk_switch_ports

from meraki_usecase.restconf.switch_ports import get_switch_ports_statuses as rest_switch_ports, get_device as rest_get_device
from meraki_usecase.sdk.switch_ports import get_switch_ports_statuses as sdk_switch_ports, get_device as sdk_get_device

from meraki_usecase.restconf.health import get_switch_health as rest_switch_health
from meraki_usecase.sdk.health import get_switch_health as sdk_switch_health


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




def main() -> None:
    parser = argparse.ArgumentParser(prog="meraki-usecase")
    parser.add_argument("--mode", choices=["rest", "sdk"], default="rest")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_orgs = sub.add_parser("orgs", help="List orgs (name + id)")
    p_orgs.add_argument("--limit", type=int, default=200)

    p_inv = sub.add_parser("inventory", help="List inventory for MERAKI_ORG_ID")
    p_inv.add_argument("--limit", type=int, default=200)

    p_health = sub.add_parser("switch-health", help="Switch health (online/offline) for a network")
    p_health.add_argument("--network-id", help="Override MERAKI_NETWORK_ID from .env")
    p_health.add_argument("--limit", type=int, default=200)

    p_ap = sub.add_parser("ap-health", help="Access Point health for MERAKI_NETWORK_ID")
    p_ap.add_argument("--network-id", help="Override MERAKI_NETWORK_ID from .env")
    p_ap.add_argument("--limit", type=int, default=200)

    p_sp = sub.add_parser("switch-ports", help="Show port statuses for one switch or all switches in a network")
    p_sp.add_argument("--serial", help="Switch serial (e.g. Q2XX-....)")
    p_sp.add_argument("--all", action="store_true", help="Get ports for all switches in MERAKI_NETWORK_ID")
    p_sp.add_argument("--network-id", help="Override MERAKI_NETWORK_ID from .env (used with --all)")
    p_sp.add_argument("--limit", type=int, default=200)




    args = parser.parse_args()
    settings = Settings()

    if args.mode == "rest":
        client = MerakiRestClient(
            base_url=settings.base_url,
            api_key=settings.api_key,
            timeout_s=settings.timeout_s,
            max_retries=settings.max_retries,
        )

        if args.cmd == "orgs":
            org_map = rest_org_map(client)
            items = list(org_map.items())[: args.limit]
            rows = [[name, oid] for name, oid in items]
            print_table(["Name", "Org ID"], rows, [55, 22])

        elif args.cmd == "inventory":
            devs = rest_inventory(client, settings.org_id)[: args.limit]
            rows = [[d.get("serial"), d.get("model"), d.get("networkId"), d.get("claimedAt")] for d in devs]
            print_table(["Serial", "Model", "Network ID", "Claimed At"], rows, [16, 10, 22, 25])

        elif args.cmd == "switch-health":
            network_id = args.network_id or settings.network_id
            devs = rest_switch_health(client, settings.org_id, network_id)[: args.limit]
            rows = [[d.get("name"), d.get("serial"), d.get("model"), d.get("status"), d.get("lastReportedAt")] for d in devs]
            print_table(["Name", "Serial", "Model", "Status", "Last Reported"], rows, [28, 16, 10, 10, 25])
        
        elif args.cmd == "ap-health":
            network_id = args.network_id or settings.network_id
            devs = rest_ap_health(client, settings.org_id, network_id)[: args.limit]
            rows = [[d.get("name"), d.get("serial"), d.get("model"), d.get("status"), d.get("lastReportedAt")] for d in devs]
            print_table(["Name", "Serial", "Model", "Status", "Last Reported"], rows, [28, 16, 10, 10, 25])
        
        elif args.cmd == "switch-ports":
            if not args.all and not args.serial:
                raise SystemExit("Provide either --serial <SERIAL> or --all")

            switches = []
            if args.all:
                network_id = args.network_id or settings.network_id
                # returns list of switch device statuses with name+serial
                switches = rest_switch_health(client, settings.org_id, network_id)
                # keep only items that actually have a serial
                switches = [s for s in switches if s.get("serial")]
            else:
                serial = args.serial
                dev = rest_get_device(client, serial)
                switches = [{"serial": serial, "name": dev.get("name") or dev.get("mac") or ""}]

            rows = []
            for sw in switches:
                serial = sw.get("serial")
                sw_name = sw.get("name", "")
                ports = rest_switch_ports(client, serial)

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

            rows = rows[: args.limit]
            print_table(
                ["Switch", "Serial", "Port", "Status", "Uplink", "Speed", "Duplex", "PoE", "Clients", "STP", "Errors", "Warnings"],
                rows,
                [22, 16, 5, 12, 6, 10, 6, 5, 7, 12, 6, 8],
            )




    else:  # sdk
        dashboard = build_dashboard(settings)

        if args.cmd == "orgs":
            org_map = sdk_org_map(dashboard)
            items = list(org_map.items())[: args.limit]
            rows = [[name, oid] for name, oid in items]
            print_table(["Name", "Org ID"], rows, [55, 22])

        elif args.cmd == "inventory":
            devs = sdk_inventory(dashboard, settings.org_id)[: args.limit]
            rows = [[d.get("serial"), d.get("model"), d.get("networkId"), d.get("claimedAt")] for d in devs]
            print_table(["Serial", "Model", "Network ID", "Claimed At"], rows, [16, 10, 22, 25])

        elif args.cmd == "switch-health":
            network_id = args.network_id or settings.network_id
            devs = sdk_switch_health(dashboard, settings.org_id, network_id)[: args.limit]
            rows = [[d.get("name"), d.get("serial"), d.get("model"), d.get("status"), d.get("lastReportedAt")] for d in devs]
            print_table(["Name", "Serial", "Model", "Status", "Last Reported"], rows, [28, 16, 10, 10, 25])
        
        elif args.cmd == "ap-health":
            network_id = args.network_id or settings.network_id
            devs = sdk_ap_health(dashboard, settings.org_id, network_id)[: args.limit]
            rows = [[d.get("name"), d.get("serial"), d.get("model"), d.get("status"), d.get("lastReportedAt")] for d in devs]
            print_table(["Name", "Serial", "Model", "Status", "Last Reported"], rows, [28, 16, 10, 10, 25])
        
        elif args.cmd == "switch-ports":
            if not args.all and not args.serial:
                raise SystemExit("Provide either --serial <SERIAL> or --all")

            switches = []
            if args.all:
                network_id = args.network_id or settings.network_id
                switches = sdk_switch_health(dashboard, settings.org_id, network_id)
                switches = [s for s in switches if s.get("serial")]
            else:
                serial = args.serial
                dev = sdk_get_device(dashboard, serial)
                switches = [{"serial": serial, "name": dev.get("name") or dev.get("mac") or ""}]

            rows = []
            for sw in switches:
                serial = sw.get("serial")
                sw_name = sw.get("name", "")
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

            rows = rows[: args.limit]
            print_table(
                ["Switch", "Serial", "Port", "Status", "Uplink", "Speed", "Duplex", "PoE", "Clients", "STP", "Errors", "Warnings"],
                rows,
                [22, 16, 5, 12, 6, 10, 6, 5, 7, 12, 6, 8],
            )





if __name__ == "__main__":
    main()
