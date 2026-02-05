import time
import requests
import os
import json
from pathlib import Path
from typing import Any, Dict
from .job import Job
from .token_caching import (
    get_cached_jwt,
    clear_jwt,
    fetch_and_cache_jwt,
)


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


def quick_submit(
    config: Dict[str, Any],
    api_key: str,
) -> Dict[str, Any]:

    # Use cached token if still fresh
    gateway_base_url: str = "http://sgen-gateway.bigsigma.tech"
    auth_base_url: str = "http://sgen-auth.bigsigma.tech"
    timeout_s: int = 15
    min_ttl_s: int = 30

    jwt = get_cached_jwt(min_ttl_s=min_ttl_s)
    if not jwt:
        jwt = fetch_and_cache_jwt(auth_base_url, api_key, timeout_s=timeout_s)

    submit_url = gateway_base_url.rstrip("/") + "/submit"
    headers = {"Authorization": f"Bearer {jwt}", "Accept": "application/json"}

    # First attempt at submitting to gateway
    resp = requests.post(
            submit_url, 
            json=config, 
            headers=headers, 
            timeout=timeout_s,
            )

    # If bounced, refresh token once and retry
    if resp.status_code in (401, 403):
        clear_jwt()
        jwt = fetch_and_cache_jwt(auth_base_url, api_key, timeout_s=timeout_s)
        headers["Authorization"] = f"Bearer {jwt}"
        resp = requests.post(
            submit_url, 
            json=config, 
            headers=headers, 
            timeout=timeout_s,
            )

    if resp.status_code != 200:
        print("Server error status:", resp.status_code)
        print("Server error headers:", resp.headers)
        print("Server error body:", resp.text)

        resp.raise_for_status()

    return resp.json()



def submit_job(config: dict, api_key: str = None) -> Job:
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    response = requests.post(f"{BASE_URL}/v1/sgen/jobs", json=config, headers=headers)
    response.raise_for_status()
    data = response.json()

    job_id = data.get("job_id") or data.get("id")  # fallback if key changes
    if not job_id:
        raise ValueError("No job_id returned from job submission response.")

    return Job(job_id=job_id, api_key=api_key)


