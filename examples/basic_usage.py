import os
import time
import sgen

api_key = os.environ["SGEN_API_KEY"]

print("Health:", sgen.health_check())
print("RTT:", sgen.round_trip_time(), "ms")

config = sgen.load_config("config.json")
result = sgen.quick_submit(config, api_key=api_key)

print("Quick Result:", result)

job_id = result["job_id"]

current = sgen.status(job_id=job_id, api_key=api_key)
while current and current.get("status") != "completed":
    time.sleep(5)
    current = sgen.status(job_id=job_id, api_key=api_key, example_count=25)
    print(current)

final = sgen.results(job_id=job_id, api_key=api_key)
print(final)