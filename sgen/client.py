import requests
from .job import Job

BASE_URL = "https://your-cloudflare-endpoint.com"

def submit_job(config: dict, api_key: str = None) -> Job:
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    response = requests.post(f"{BASE_URL}/start-job", json=config, headers=headers)
    response.raise_for_status()
    data = response.json()
    return Job(job_id=data["job_id"], api_key=api_key)
