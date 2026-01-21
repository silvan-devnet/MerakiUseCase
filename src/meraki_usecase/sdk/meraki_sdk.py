from __future__ import annotations

import inspect
import meraki
from meraki_usecase.config import Settings

def build_dashboard(settings: Settings) -> meraki.DashboardAPI:
    base_kwargs = {
        "api_key": settings.api_key,
        "base_url": settings.base_url,
        "suppress_logging": True,
        "wait_on_rate_limit": True,
        "maximum_retries": settings.max_retries,
    }

    sig = inspect.signature(meraki.DashboardAPI.__init__)
    params = sig.parameters

    if "timeout" in params:
        base_kwargs["timeout"] = settings.timeout_s
    elif "request_timeout" in params:
        base_kwargs["request_timeout"] = settings.timeout_s
    elif "single_request_timeout" in params:
        base_kwargs["single_request_timeout"] = settings.timeout_s

    return meraki.DashboardAPI(**base_kwargs)
