import sgen
import time

print("Health:", sgen.health_check())
print("RTT:", sgen.round_trip_time(), "ms")

config = sgen.load_config("config.json")
result = sgen.quick_submit(config, api_key="YOUR_CLIENT_ID:YOUR_CLIENT_SECRET")

print("Quick Result:", result)

job_id = result["job_id"]
time.sleep(50)
new_job = sgen.results(job_id=job_id, api_key="YOUR_CLIENT_ID:YOUR_CLIENT_SECRET")
print(new_job)
