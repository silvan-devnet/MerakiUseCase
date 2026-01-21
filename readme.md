# MerakiUseCase

Small learning project showing **two ways** to call the Cisco Meraki Dashboard API:

- `restconf/` → **raw REST** using `requests` (no SDK)
- `sdk/` → using the **Meraki Python SDK**

It also includes a simple CLI to:
- list organizations
- list org inventory devices
- show “health” (online/offline + last reported) for **switches** and **access points** in a network

> Note: Meraki Dashboard API is a REST API. The folder name `restconf/` here is used as “raw REST implementation” for learning.

---

## Requirements

- Python **3.10+** (Meraki SDK requires Python >= 3.10)
- A Meraki Dashboard API key

---

## Project structure

```
MerakiUseCase/
  .env
  pyproject.toml
  src/
    meraki_usecase/
      config.py
      cli.py
      restconf/
        meraki_rest.py
        orgs.py
        inventory.py
        health.py          # switch health
        health_ap.py       # access point health
      sdk/
        meraki_sdk.py
        orgs.py
        inventory.py
        health.py          # switch health
        health_ap.py       # access point health
```

---

## Setup

### 1) Create a virtual environment

From the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python --version
```

Make sure it prints Python 3.10+.

### 2) Install dependencies

```bash
pip install -U pip
pip install -e .
```

> If you previously hit the LibreSSL/urllib3 warning on macOS, pinning `urllib3<2` in `pyproject.toml` avoids that.

---

## Configure `.env`

Create a `.env` file in the repo root:

```dotenv
MERAKI_DASHBOARD_API_KEY=YOUR_API_KEY_HERE
MERAKI_ORG_ID=YOUR_ORG_ID_HERE
MERAKI_NETWORK_ID=YOUR_NETWORK_ID_HERE

MERAKI_DASHBOARD_BASE_URL=https://api.meraki.com/api/v1
MERAKI_REQUEST_TIMEOUT=30
MERAKI_MAX_RETRIES=5
```

### How to get ORG_ID quickly
Run:

```bash
meraki-usecase --mode rest orgs
```

Copy the org id you want into `MERAKI_ORG_ID`.

### How to get NETWORK_ID
You can get it from the Meraki Dashboard UI (Network details) or via API (not implemented in this small starter).

---

## Usage (CLI)

The CLI supports two modes:

- `--mode rest` (raw REST using requests)
- `--mode sdk` (Meraki Dashboard SDK)

### List organizations

```bash
meraki-usecase --mode rest orgs
meraki-usecase --mode sdk  orgs --limit 20
```

### Inventory devices (uses MERAKI_ORG_ID)

```bash
meraki-usecase --mode rest inventory
meraki-usecase --mode sdk  inventory --limit 50
```

### Switch health (uses MERAKI_ORG_ID + MERAKI_NETWORK_ID)

Shows switch devices in the selected network with:
- name
- serial
- model
- status
- lastReportedAt

```bash
meraki-usecase --mode rest switch-health
meraki-usecase --mode sdk  switch-health --limit 50
```

Override the network id from CLI (optional):

```bash
meraki-usecase --mode rest switch-health --network-id <NETWORK_ID>
```

### Access point health (uses MERAKI_ORG_ID + MERAKI_NETWORK_ID)

Same style as switch health but filtered to wireless devices:

```bash
meraki-usecase --mode rest ap-health
meraki-usecase --mode sdk  ap-health --limit 50
```

Override the network id:

```bash
meraki-usecase --mode sdk ap-health --network-id <NETWORK_ID>
```

---

## Notes / gotchas

- Inventory endpoints can paginate in large orgs. This learning version may be “good enough” for many cases; if you see missing devices, add full pagination handling.
- Org names may not be unique across all orgs. For automation, prefer using org IDs as keys.
- Keep your API key secret. Do not commit `.env` to git.

---

## Troubleshooting

### `meraki.exceptions.PythonVersionError`
You’re running Python < 3.10. Create your venv with Python 3.10+ and reinstall.

### Import errors
Ensure folders are inside the package:

```
src/meraki_usecase/restconf
src/meraki_usecase/sdk
```

and each folder contains an `__init__.py` (optional in modern Python, but helpful with tooling).

---

## Next ideas
- Export outputs to JSON/CSV (`--json out.json`, `--csv out.csv`)
- Add `networks` command to fetch network list and pick `MERAKI_NETWORK_ID`
- Add deeper “health”:
  - switch ports (errors, PoE, STP)
  - AP RF metrics and client counts
