import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from .request import gateway_request

BASE_URL = os.getenv("SGEN_API_URL", "https://sgen-gateway.bigsigma.tech")
AUTH_URL = os.getenv("SGEN_AUTH_URL", "https://sgen-auth.bigsigma.tech")


def health_check() -> Dict[str, Any]:
    response = requests.get(f"{BASE_URL}/health", timeout=15)
    response.raise_for_status()
    return response.json()


def round_trip_time() -> float:
    start = time.time()
    response = requests.get(f"{BASE_URL}/health", timeout=15)
    response.raise_for_status()
    end = time.time()
    return round((end - start) * 1000, 2)


def load_config(path: str) -> Dict[str, Any]:
    p = Path(path)

    if p.is_dir():
        config_path = p / "config.json"
    else:
        config_path = p

    if not config_path.exists():
        raise FileNotFoundError(f"No config.json found at {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    if not isinstance(config.get("n"), int) or not isinstance(config.get("k"), int):
        raise ValueError("Config must include integer fields 'n' and 'k'")

    return config


def quick_submit(config: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    resp = gateway_request(
        method="POST",
        gateway_base_url=BASE_URL,
        auth_base_url=AUTH_URL,
        api_key=api_key,
        path="/submit",
        json_body=config,
        timeout_s=15,
        min_ttl_s=30,
    )
    resp.raise_for_status()
    return resp.json()


def results(job_id: str, api_key: str) -> Optional[Dict[str, Any]]:
    resp = gateway_request(
        method="GET",
        gateway_base_url=BASE_URL,
        auth_base_url=AUTH_URL,
        api_key=api_key,
        path=f"/results/{job_id}",
        json_body=None,
        timeout_s=15,
        min_ttl_s=30,
    )

    if resp.status_code == 200:
        return resp.json()

    if resp.status_code in (202, 404, 409):
        return None

    resp.raise_for_status()
    return None


def status(job_id: str, api_key: str, example_count: int = 1) -> Optional[Dict[str, Any]]:
    if not 1 <= example_count <= 50:
        raise ValueError("example_count must be between 1 and 50")

    resp = gateway_request(
        method="GET",
        gateway_base_url=BASE_URL,
        auth_base_url=AUTH_URL,
        api_key=api_key,
        path=f"/status/{job_id}",
        json_body=None,
        params={"example_count": example_count},
        timeout_s=15,
        min_ttl_s=30,
    )

    if resp.status_code == 200:
        return resp.json()

    if resp.status_code in (202, 404, 409):
        return None

    resp.raise_for_status()
    return None