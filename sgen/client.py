import time
import requests
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from .job import Job
from .request import gateway_request


BASE_URL = os.getenv("SGEN_API_URL", "https://sgen-gateway.bigsigma.tech")

def health_check():
    response = requests.get(f"{BASE_URL}/health")
    print("Calling:", response.url)
    print("Status:", response.status_code)
    print("Headers:", response.headers)
    print("Body:", response.text)

    return response.json()


def round_trip_time() -> float:
    start = time.time()
    requests.get(f"{BASE_URL}/health")
    end = time.time()
    return round((end - start) * 1000, 2) #return ms


def load_config(path: str) -> dict:
    p = Path(path)

    if p.is_dir():
        config_path = p / "config.json"
    else:
        config_path = p

    if not config_path.exists():
        raise FileNotFoundError(f"No config.json found at {config_path}")

    with config_path.open("r") as f:
        config = json.load(f)

    # Basic validation
    if not isinstance(config.get("n"), int) or not isinstance(config.get("k"), int):
        raise ValueError("Config must include integer fields 'n' and 'k'")

    return config


def quick_submit(config: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    resp = gateway_request(
        method="POST",
        gateway_base_url="http://sgen-gateway.bigsigma.tech",
        auth_base_url="http://sgen-auth.bigsigma.tech",
        api_key=api_key,
        path="/submit",
        json_body=config,
        timeout_s=15,
        min_ttl_s=30,
    )

    if resp.status_code != 200:
        print("Server error status:", resp.status_code)
        print("Server error headers:", resp.headers)
        print("Server error body:", resp.text)
        resp.raise_for_status()

    return resp.json()

def results(job_id: str, api_key: str) -> Optional[Dict[str,any]]:
    resp = gateway_request(
        method="GET",
        gateway_base_url="http://sgen-gateway.bigsigma.tech",
        auth_base_url="http://sgen-auth.bigsigma.tech",
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

    print("Server error status:", resp.status_code)
    print("Server error headers:", resp.headers)
    print("Server error body:", resp.text)
    resp.raise_for_status()
    return None

