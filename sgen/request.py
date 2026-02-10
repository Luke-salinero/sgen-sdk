from typing import Any, Dict, Optional
import requests

from .token_caching import get_cached_jwt, fetch_and_cache_jwt, clear_jwt

def gateway_request(
    *,
    method: str,
    gateway_base_url: str,
    auth_base_url: str,
    api_key: str,
    path: str,
    json_body: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout_s: int = 15,
    min_ttl_s: int = 30,
) -> requests.Response:

    jwt = get_cached_jwt(min_ttl_s=min_ttl_s)
    if not jwt:
        jwt = fetch_and_cache_jwt(auth_base_url, api_key, timeout_s=timeout_s)

    url = gateway_base_url.rstrip("/") + path
    headers = {"Authorization": f"Bearer {jwt}", "Accept": "application/json"}

    resp = requests.request(
        method=method,
        url=url,
        headers=headers,
        json=json_body,
        params=params,
        timeout=timeout_s,
    )

    if resp.status_code in (401, 403):
        clear_jwt()
        jwt = fetch_and_cache_jwt(auth_base_url, api_key, timeout_s=timeout_s)
        headers["Authorization"] = f"Bearer {jwt}"

        resp = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json_body,
            params=params,
            timeout=timeout_s,
        )

    return resp