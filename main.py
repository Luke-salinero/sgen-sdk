import os
import sys
import time

import sgen

API_KEY = os.getenv("SGEN_API_KEY")
if not API_KEY:
    sys.exit("Set SGEN_API_KEY to a client_id:client_secret API key before running this script.")

print("Health:", sgen.health_check())
print("RTT:", sgen.round_trip_time(), "ms")

config = sgen.load_config("config.json")
result = sgen.quick_submit(config, api_key=API_KEY)

print("Quick Result:", result)

job_id = result["job_id"]

status = sgen.status(job_id=job_id, api_key=API_KEY)
while status["status"] != "completed":
    time.sleep(5)
    status = sgen.status(job_id=job_id, api_key=API_KEY, example_count=25)
    print(status)

time.sleep(2)
new_job = sgen.results(job_id=job_id, api_key=API_KEY)
#print(new_job)
