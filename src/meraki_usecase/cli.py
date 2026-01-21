from __future__ import annotations

import argparse
from typing import Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


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

from meraki_usecase.restconf.wifi_signal import get_wifi_signal_quality_by_client as rest_wifi_signal
from meraki_usecase.sdk.wifi_signal import get_wifi_signal_quality_by_client as sdk_wifi_signal

from meraki_usecase.restconf.network_clients import get_network_clients as rest_network_clients
from meraki_usecase.sdk.network_clients import get_network_clients as sdk_network_clients


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

def _snr_style(snr_val):
    if snr_val is None:
        return ("", "dim")
    try:
        snr = int(snr_val)
    except Exception:
        return (str(snr_val), "dim")

    if snr >= 40:
        return (str(snr), "bold green")
    if snr >= 25:
        return (str(snr), "green")
    if snr >= 20:
        return (str(snr), "yellow")
    return (str(snr), "red")


def _rssi_style(rssi_val):
    if rssi_val is None:
        return ("", "dim")
    try:
        rssi = int(rssi_val)
    except Exception:
        return (str(rssi_val), "dim")

    # RSSI is negative dBm; closer to 0 is better
    if rssi >= -65:
        return (str(rssi), "bold green")
    if -71 <= rssi <= -66:
        return (str(rssi), "green")
    if -77 <= rssi <= -72:
        return (str(rssi), "yellow")
    return (str(rssi), "red")


def print_wifi_signal_rich(rows, *, title="Wi-Fi Signal Quality by Client"):
    console = Console()

    legend = (
        "[b]SNR (dB)[/b]\n"
        "  [bold green]Excellent[/bold green]  ≥ 40\n"
        "  [green]Good[/green]       25–39 (≥25 recommended for voice)\n"
        "  [yellow]Fair[/yellow]       20–24 (≥20 recommended for data)\n"
        "  [red]Poor[/red]       < 20\n\n"
        "[b]RSSI (dBm)[/b]\n"
        "  [bold green]Excellent[/bold green]  ≥ -65\n"
        "  [green]Good[/green]       -66 to -71\n"
        "  [yellow]Fair[/yellow]       -72 to -77\n"
        "  [red]Poor[/red]       ≤ -78\n"
    )
    console.print(Panel(legend, title="Legend", expand=False))

    table = Table(title=title, show_lines=False)
    table.add_column("Client ID", style="cyan", no_wrap=True)
    table.add_column("Client MAC", no_wrap=True)
    table.add_column("Network", overflow="fold")
    table.add_column("Network ID", overflow="fold")
    table.add_column("SNR", justify="right")
    table.add_column("RSSI", justify="right")

    for r in rows:
        client_id = r.get("client_id", "")
        client_mac = r.get("client_mac", "")
        net_name = r.get("network_name", "")
        net_id = r.get("network_id", "")

        snr_text, snr_style = _snr_style(r.get("snr"))
        rssi_text, rssi_style = _rssi_style(r.get("rssi"))

        table.add_row(
            str(client_id),
            str(client_mac),
            str(net_name),
            str(net_id),
            f"[{snr_style}]{snr_text}[/{snr_style}]",
            f"[{rssi_style}]{rssi_text}[/{rssi_style}]",
        )

    console.print(table)

def _kb_to_mb(v) -> float:
    try:
        return float(v) / 1024.0
    except Exception:
        return 0.0

def _kb_to_mb_str(v) -> str:
    mb = _kb_to_mb(v)
    return "" if mb == 0 else f"{mb:.1f}"

def print_network_clients_rich(rows, *, title: str, timespan_s: int) -> None:
    console = Console()

    legend = (
        f"[b]Legend[/b]\n"
        f"- Timespan: {timespan_s} seconds\n"
        f"- Usage columns are [b]MB[/b] (converted from Meraki usage fields in KB)\n"
        f"- Name is derived from description/user/dhcpHostname/mdnsName (first non-empty)\n"
    )
    console.print(Panel(legend, title="Info", expand=False))

    table = Table(
        title=title,
        row_styles=["none", "dim"],   # zebra stripes (alternating style)
    )
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("MAC", no_wrap=True)
    table.add_column("Name", overflow="fold")
    table.add_column("Status", no_wrap=True)
    table.add_column("Sent MB", justify="right")
    table.add_column("Recv MB", justify="right")
    table.add_column("Total MB", justify="right")
    table.add_column("Last Seen", justify="right")

    for r in rows:
        usage = r.get("usage") or {}
        sent_mb = _kb_to_mb(usage.get("sent"))
        recv_mb = _kb_to_mb(usage.get("recv"))
        total_mb = sent_mb + recv_mb

        table.add_row(
            str(r.get("id", "")),
            str(r.get("mac", "")),
            str(r.get("name", "")),
            str(r.get("status", "")),
            f"{sent_mb:.1f}",
            f"{recv_mb:.1f}",
            f"{total_mb:.1f}",
            str(r.get("lastSeen", "")),
        )

    console.print(table)





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

    p_ws = sub.add_parser("wifi-signal", help="Wireless signal quality by client (org-wide, optional network/AP filters)")
    p_ws.add_argument("--timespan", type=int, default=86400, help="Seconds (default: 86400 = 24h)")
    p_ws.add_argument("--network-id", help="Override MERAKI_NETWORK_ID from .env")
    p_ws.add_argument("--serials", help="Comma-separated AP serials to filter (e.g. Q2XX-...,Q2YY-...)")
    p_ws.add_argument("--limit", type=int, default=200)

    p_nc = sub.add_parser("network-clients", help="List clients in a network with usage for the timespan (default 24h)")
    p_nc.add_argument("--timespan", type=int, default=86400, help="Seconds (default: 86400 = 24h)")
    p_nc.add_argument("--network-id", help="Override MERAKI_NETWORK_ID from .env")
    p_nc.add_argument("--conn", choices=["wired", "wireless", "all"], default="all", help="Filter by recent connection type")
    p_nc.add_argument("--limit", type=int, default=200)

    p_nc.add_argument("--sort", choices=["total", "sent", "recv", "name", "mac", "lastSeen"], default="total",
                  help="Sort field (default: total)")
    p_nc.add_argument("--top", type=int, default=0,
                    help="Show only top N after sorting (0 = no top filter)")
    p_nc.add_argument("--desc", action="store_true",
                    help="Sort descending (default for total/sent/recv is descending anyway)")






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

        elif args.cmd == "wifi-signal":
            network_id = args.network_id or settings.network_id
            serials = [s.strip() for s in args.serials.split(",")] if args.serials else None

            data = rest_wifi_signal(
                client,
                settings.org_id,
                timespan=args.timespan,
                network_id=network_id,
                serials=serials,
            )[: args.limit]

            # Response fields can evolve; we print common ones safely
            rows = []
            for r in data:
                client = r.get("client") or {}
                network = r.get("network") or {}

                rows.append({
                    "client_id": client.get("id", ""),
                    "client_mac": client.get("mac", ""),
                    "network_name": network.get("name", ""),
                    "network_id": network.get("id", ""),
                    "snr": r.get("snr", None),
                    "rssi": r.get("rssi", None),
                })

            print_wifi_signal_rich(rows)

        elif args.cmd == "network-clients":
            network_id = args.network_id or settings.network_id

            conn_types = None
            if args.conn == "wired":
                conn_types = ["Wired"]
            elif args.conn == "wireless":
                conn_types = ["Wireless"]

            data = rest_network_clients(
                client,
                network_id,
                timespan=args.timespan,
                connection_types=conn_types,
            )[: args.limit]

            rows = []
            for c in data:
                name = (
                    c.get("description")
                    or c.get("user")
                    or c.get("dhcpHostname")
                    or c.get("mdnsName")
                    or ""
                )
                rows.append({
                    "id": c.get("id", ""),
                    "mac": c.get("mac", ""),
                    "name": name,
                    "status": c.get("status", ""),
                    "usage": c.get("usage", {}) or {},
                    "lastSeen": c.get("lastSeen", ""),
                })
            def _sort_key(row, field: str):
                usage = row.get("usage") or {}
                if field == "sent":
                    return _kb_to_mb(usage.get("sent"))
                if field == "recv":
                    return _kb_to_mb(usage.get("recv"))
                if field == "total":
                    return _kb_to_mb(usage.get("sent")) + _kb_to_mb(usage.get("recv"))
                if field == "name":
                    return (row.get("name") or "").lower()
                if field == "mac":
                    return (row.get("mac") or "").lower()
                if field == "lastSeen":
                    # ISO-ish timestamps sort lexicographically fine when present
                    return row.get("lastSeen") or ""
                return 0

            # default direction: numeric sorts descending
            numeric = args.sort in ("total", "sent", "recv")
            reverse = args.desc or numeric

            rows.sort(key=lambda r: _sort_key(r, args.sort), reverse=reverse)

            if args.top and args.top > 0:
                rows = rows[: args.top]


            print_network_clients_rich(
                rows,
                title=f"Network Clients (REST) — {network_id}",
                timespan_s=args.timespan,
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


        elif args.cmd == "wifi-signal":
            network_id = args.network_id or settings.network_id
            serials = [s.strip() for s in args.serials.split(",")] if args.serials else None

            data = sdk_wifi_signal(
                dashboard,
                settings.org_id,
                timespan=args.timespan,
                network_id=network_id,
                serials=serials,
            )[: args.limit]

            rows = []
            for r in data:
                client = r.get("client") or {}
                network = r.get("network") or {}

                rows.append({
                    "client_id": client.get("id", ""),
                    "client_mac": client.get("mac", ""),
                    "network_name": network.get("name", ""),
                    "network_id": network.get("id", ""),
                    "snr": r.get("snr", None),
                    "rssi": r.get("rssi", None),
                })

            print_wifi_signal_rich(rows)

        elif args.cmd == "network-clients":
            network_id = args.network_id or settings.network_id

            conn_types = None
            if args.conn == "wired":
                conn_types = ["Wired"]
            elif args.conn == "wireless":
                conn_types = ["Wireless"]

            data = sdk_network_clients(
                dashboard,
                network_id,
                timespan=args.timespan,
                connection_types=conn_types,
            )[: args.limit]

            rows = []
            for c in data:
                name = (
                    c.get("description")
                    or c.get("user")
                    or c.get("dhcpHostname")
                    or c.get("mdnsName")
                    or ""
                )
                rows.append({
                    "id": c.get("id", ""),
                    "mac": c.get("mac", ""),
                    "name": name,
                    "status": c.get("status", ""),
                    "usage": c.get("usage", {}) or {},
                    "lastSeen": c.get("lastSeen", ""),
                })

            def _sort_key(row, field: str):
                usage = row.get("usage") or {}
                if field == "sent":
                    return _kb_to_mb(usage.get("sent"))
                if field == "recv":
                    return _kb_to_mb(usage.get("recv"))
                if field == "total":
                    return _kb_to_mb(usage.get("sent")) + _kb_to_mb(usage.get("recv"))
                if field == "name":
                    return (row.get("name") or "").lower()
                if field == "mac":
                    return (row.get("mac") or "").lower()
                if field == "lastSeen":
                    # ISO-ish timestamps sort lexicographically fine when present
                    return row.get("lastSeen") or ""
                return 0

            # default direction: numeric sorts descending
            numeric = args.sort in ("total", "sent", "recv")
            reverse = args.desc or numeric

            rows.sort(key=lambda r: _sort_key(r, args.sort), reverse=reverse)

            if args.top and args.top > 0:
                rows = rows[: args.top]

            print_network_clients_rich(
                rows,
                title=f"Network Clients (SDK) — {network_id}",
                timespan_s=args.timespan,
            )

if __name__ == "__main__":
    main()
