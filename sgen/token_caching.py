import base64
import json
import time
from dataclasses import dataclass
from typing import Optional
import requests
import os


@dataclass
class TokenCache:
    token: Optional[str] = None
    exp: int = 0 


TOKEN = TokenCache()


def b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def jwt_exp_unverified(jwt: str) -> int:
    parts = jwt.split(".")
    if len(parts) < 2:
        return 0
    payload = json.loads(b64url_decode(parts[1]).decode("utf-8"))
    exp = payload.get("exp", 0)
    try:
        return int(exp)
    except Exception:
        return 0


def get_cached_jwt(min_ttl_s: int = 30) -> Optional[str]:
    """
    Return cached token only if it is valid 
    for at least min_ttl_s more seconds.
    """
    now = int(time.time())
    if TOKEN.token and TOKEN.exp and now < (TOKEN.exp - min_ttl_s):
        return TOKEN.token
    return None


def cache_jwt(jwt: str) -> None:
    TOKEN.token = jwt
    TOKEN.exp = jwt_exp_unverified(jwt)


def clear_jwt() -> None:
    TOKEN.token = None
    TOKEN.exp = 0

def post_mint(base_url: str,
                api_key: str, 
                timeout_s: int = 15,
                ) -> requests.Response:
    mint_path = os.getenv("MINT_PATH", "/v1/mint")

    headers = {"Authorization": f"ApiKey {api_key.strip()}"}

    last_resp: Optional[requests.Response] = None
    if not mint_path.startswith("/"):
        mint_path = "/" + mint_path
    url = base_url.rstrip("/") + mint_path

    try:
        resp = requests.post(
                url, 
                json={}, 
                headers=headers, 
                timeout=timeout_s
                )
    except requests.RequestException:
        raise RuntimeError("Could not reach auth server or mint endpoint.")

    last_resp = resp
    if resp.status_code != 404:
        return resp

    if last_resp is None:
        raise RuntimeError("Could not reach auth server or mint endpoint.")
    return last_resp


def fetch_and_cache_jwt(auth_base_url: str, 
                        api_key: str, timeout_s: 
                        int = 15
                        ) -> str:
    resp = post_mint(auth_base_url, api_key, timeout_s=timeout_s)

    if resp.status_code != 200:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise requests.HTTPError(
            f"Mint failed ({resp.status_code}): {detail}", 
            response=resp
            )

    data = resp.json()
    jwt = data.get("access_token")
    if not jwt:
        raise RuntimeError(
            f"""Mint response missing access_token. 
            Keys: {list(data.keys())}"""
            )

    cache_jwt(jwt)
    return jwt