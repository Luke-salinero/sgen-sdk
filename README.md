# sgen-sdk

Python client library for submitting jobs to the SGen platform and polling
for status/results through `sgen-gateway`.

## Install

```bash
pip install -r requirements.txt
```

Requires `requests>=2.32.5`.

## Authentication

Every call takes an `api_key` in `client_id:client_secret` form (minted via
`sgen-auth`'s `/v1/keys` endpoint). The SDK exchanges it for a short-lived
JWT against `sgen-auth`'s `/v1/mint` endpoint and caches that JWT in memory
for the rest of the process (`sgen/token_caching.py`); it re-mints
automatically on a 401/403.

**Never hardcode an API key in source.** Read it from an environment
variable or secret store, e.g. `os.getenv("SGEN_API_KEY")`.

## Usage

```python
import os
import sgen

api_key = os.environ["SGEN_API_KEY"]

config = sgen.load_config("config.json")  # requires integer "n" and "k"
result = sgen.quick_submit(config, api_key=api_key)
job_id = result["job_id"]

status = sgen.status(job_id=job_id, api_key=api_key, example_count=5)
results = sgen.results(job_id=job_id, api_key=api_key)  # None until completed
```

`main.py` is a runnable end-to-end example; it reads `SGEN_API_KEY` from the
environment and `config.json` (a sample `n=45, k=15` search) from the repo
root.

## API

| Function | Description |
| -------- | ----------- |
| `health_check()` | `GET /health` on the gateway; returns the parsed JSON body. |
| `round_trip_time()` | Round-trip latency to `/health` in milliseconds. |
| `load_config(path)` | Loads and minimally validates a job config JSON file (`n`/`k` must be ints). |
| `quick_submit(config, api_key)` | `POST /submit` — submits a job, returns `{job_id, status, mode, ...}`. |
| `status(job_id, api_key, example_count=1)` | `GET /status/{job_id}` — progress summary plus up to `example_count` example candidates once running. |
| `results(job_id, api_key)` | `GET /results/{job_id}` — full result payload once the job is `completed`; `None` while pending/running/failed. |

Gateway/auth base URLs default to `https://sgen-gateway.bigsigma.tech` and
`https://sgen-auth.bigsigma.tech`, overridable via the `SGEN_API_URL` env var
(`client.py`) — note `quick_submit`/`status`/`results` currently hardcode the
gateway/auth hosts they call rather than reading `SGEN_API_URL`.

## Known issues

- `sgen/job.py`'s `Job` class is unfinished: it points at a placeholder
  `BASE_URL` and a `/job-status` path that don't correspond to any current
  gateway route (`/status/{job_id}` and `/results/{job_id}` are the real
  ones). Use the module-level `status()`/`results()` functions instead.

## Tests

```bash
python -m unittest discover -s test
```
