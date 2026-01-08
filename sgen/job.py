import time
import requests

BASE_URL = "https://your-cloudflare-endpoint.com"

class Job:
    def __init__(self, job_id: str, api_key: str = None):
        self.job_id = job_id
        self.api_key = api_key

    def get_status(self) -> dict:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        resp = requests.get(f"{BASE_URL}/job-status", params={"job_id": self.job_id}, headers=headers)
        return resp.json()

    def get_result(self, poll: bool = True, interval: int = 2, timeout: int = 300):
        start = time.time()
        while poll and (time.time() - start) < timeout:
            status = self.get_status()
            if status["status"] == "done":
                return status.get("result")
            elif status["status"] == "failed":
                raise Exception("Job failed.")
            time.sleep(interval)
        raise TimeoutError("Job did not complete in time.")
