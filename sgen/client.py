import time
import requests
import os
import json
from pathlib import Path
from .job import Job


BASE_URL = os.getenv("SGEN_API_URL", "https://sgen-api.bigsigma.tech")

def health_check():
    response = requests.get(f"{BASE_URL}/health")
    return response.json()


def round_trip_time() -> float:
    start = time.time()
    requests.get(f"{BASE_URL}/health")
    end = time.time()
    return round((end - start) * 1000, 2)  # return ms


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


def quick_submit(config: dict, api_key: str = None):
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    response = requests.post(f"{BASE_URL}/submit", json=config, headers=headers)

    if response.status_code != 200:
        print("Server error response:", response.json())
        response.raise_for_status()

    return response.json()



def submit_job(config: dict, api_key: str = None) -> Job:
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    response = requests.post(f"{BASE_URL}/v1/sgen/jobs", json=config, headers=headers)
    response.raise_for_status()
    data = response.json()

    job_id = data.get("job_id") or data.get("id")  # fallback if key changes
    if not job_id:
        raise ValueError("No job_id returned from job submission response.")

    return Job(job_id=job_id, api_key=api_key)


