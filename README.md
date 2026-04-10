# sgen

Python SDK for submitting and tracking SGEN jobs.

SGEN is a Python SDK for submitting graph-search jobs to the SGEN gateway, polling them asynchronously, and retrieving final results. It is designed for workflows where a search is defined by a JSON configuration containing a bit-encoded graph search space and optional pruning/finding masks.

## Installation

Install the SDK with pip:

```bash
pip install sgen
```

Verify installation:

```bash
python -c "import sgen; print('SGEN installed')"
```

## What SGEN Does

SGEN searches a space of candidate graphs represented as **k-of-n bitmasks**.

Each candidate graph is encoded as a binary mask where each bit corresponds to a possible undirected edge:

- `n` = total possible edges in the encoding
- `k` = number of edges selected in each candidate
- each candidate graph is a bitmask with exactly `k` bits set

This makes it possible to efficiently enumerate and test large families of graphs.

## Core Workflow

The standard SGEN workflow is:

1. Create or load a config
2. Submit the config with `quick_submit()`
3. Poll progress with `status()`
4. Retrieve final output with `results()`

## Quick Start

Here is a minimal end-to-end workflow:

```python
import os
import time
import sgen

API_KEY = os.environ["SGEN_API_KEY"]

# Load configuration
config = sgen.load_config("config.json")

# Submit job
job = sgen.quick_submit(config, API_KEY)
job_id = job["job_id"]

print("Submitted:", job_id)

# Poll until complete
while True:
    st = sgen.status(job_id, API_KEY)

    if st is None:
        time.sleep(5)
        continue

    if st["status"] == "completed":
        print("Completed:", st)
        break

    if st["status"] == "failed":
        print("Failed:", st.get("error"))
        break

    print("Progress:", st)
    time.sleep(5)

# Retrieve final results
res = sgen.results(job_id, API_KEY)

if res:
    print("Results:", res)
```

## Package API

The SDK currently exposes these top-level functions and classes:

- `sgen.load_config(path)`
- `sgen.quick_submit(config, api_key)`
- `sgen.status(job_id, api_key, example_count=1)`
- `sgen.results(job_id, api_key)`
- `sgen.health_check()`
- `sgen.round_trip_time()`
- `sgen.Job`

## Authentication

Pass your API key into submission and polling calls:

```python
import os

API_KEY = os.environ["SGEN_API_KEY"]
```

Recommended shell setup:

```bash
export SGEN_API_KEY="your-api-key"
```

Do not hardcode live API keys into source files or commit them to Git.

## Configuration Files

SGEN requires a JSON configuration describing the search space.

### Example `config.json`

```json
{
  "n": 15,
  "k": 8,
  "existential": true,
  "prune_masks": [
    "0b000001001100111",
    "0b000010010101011"
  ],
  "find_masks": [
    "0b111000111000000",
    "0b111111000000000"
  ],
  "ranges": [
    [
      "0b000000000111111",
      "0b111111000000000"
    ]
  ]
}
```

At minimum:

- `n` must be an integer
- `k` must be an integer

## Understanding the Bit Encoding

For a graph with `num_nodes` vertices:

- there are `num_nodes * (num_nodes - 1) / 2` possible undirected edges
- each edge is assigned a unique bit position
- each candidate graph is represented as a single bitmask integer
- a bit value of `1` means the edge is present
- a bit value of `0` means the edge is absent

SGEN searches masks with exactly `k` bits set.

### Example: 4 Nodes

Possible edges:

```text
(0,1)
(0,2)
(0,3)
(1,2)
(1,3)
(2,3)
```

So:

```text
n = 6
```

If `k = 2`, SGEN searches all masks with exactly two selected edges.

Example:

```text
0b010001
```

This represents a graph where exactly two edges are present.

## Config Structure

A typical generated config looks like this:

```json
{
  "n": 28,
  "k": 12,
  "block_size": 3,
  "existential": false,
  "prune_masks": ["0b001010...", "0b010001..."],
  "find_masks": [],
  "ranges": [
    ["0b000000111...", "0b111000000..."]
  ]
}
```

### Config Fields

| Field | Description |
|---|---|
| `n` | Number of bits in the encoding, equal to the total possible edges. |
| `k` | Number of selected edges in each candidate. |
| `block_size` | Work chunk size used by the SGEN search scheduler. |
| `existential` | Controls existential vs exhaustive search behavior. |
| `prune_masks` | Bit patterns representing structures that should be rejected early. |
| `find_masks` | Bit patterns SGEN should attempt to find. |
| `ranges` | Search intervals within the k-of-n space. |

## Creating Configs Automatically

SGEN configs can be generated using a helper script such as `config_maker.py`.

Example:

```python
cfg = generate_config(
    num_nodes=8,
    k=22,
    block_size=3,
    existential=False,
    prune_clique_size=3
)

save_config(cfg, "./out/config8nodes3clique.json")
```

Run the generator with:

```bash
python config_maker.py
```

This writes a valid config file.

## How Pruning Works

A generator can create `prune_masks` representing forbidden substructures.

For example, setting:

```python
prune_clique_size = 3
```

can generate masks representing triangles.

If a candidate graph contains all edges of one of these masks, SGEN can reject it early, which reduces the amount of work required.

## Creating a Mask From Edges

You can also construct masks manually.

```python
def edge_index(i, j, n):
    return i * n + j - ((i + 2) * (i + 1)) // 2

def mask_from_edges(num_nodes, edges):
    mask = 0
    for i, j in edges:
        if i > j:
            i, j = j, i
        mask |= 1 << edge_index(i, j, num_nodes)
    return mask
```

Example:

```python
num_nodes = 4
edges = [(0, 1), (2, 3)]

mask = mask_from_edges(num_nodes, edges)
print(bin(mask))
```

## Minimal Manual Config Example

```python
import json

config = {
    "n": 6,
    "k": 2,
    "block_size": 1,
    "existential": False,
    "prune_masks": [],
    "find_masks": [],
    "ranges": [
        ["0b000011", "0b110000"]
    ]
}

with open("config.json", "w") as f:
    json.dump(config, f, indent=2)
```

## Submitting a Job

Use `sgen.quick_submit()` to send a configuration to the SGEN gateway.

```python
import os
import sgen

API_KEY = os.environ["SGEN_API_KEY"]

config = sgen.load_config("config.json")
job = sgen.quick_submit(config, API_KEY)

print(job)
```

### Example Submission Response

```python
{
    "job_id": "b10425d6-c8eb-4ccb-8f93-a731bbe7d616",
    "status": "Pending",
    "mode": "Live",
    "result": None,
    "error": None
}
```

### Submission Response Fields

| Field | Type | Description |
|---|---|---|
| `job_id` | `str` | Unique UUID identifying the submitted job. |
| `status` | `str` | Initial job state, usually `Pending`. |
| `mode` | `str` | Execution mode, such as `Live` or `Mock`. |
| `result` | `dict | None` | Usually `None` immediately after submission. |
| `error` | `str | None` | Error details if submission failed. |

## Polling Job Status

SGEN jobs run asynchronously. Use `status()` to monitor progress.

```python
import os
import time
import sgen

API_KEY = os.environ["SGEN_API_KEY"]

config = sgen.load_config("config.json")
job = sgen.quick_submit(config, api_key=API_KEY)
job_id = job["job_id"]

print("Submitted:", job_id)

while True:
    st = sgen.status(
        job_id=job_id,
        api_key=API_KEY,
        example_count=25
    )

    if st is None:
        time.sleep(5)
        continue

    if st["status"] == "completed":
        print("Completed:", st)
        break

    if st["status"] == "failed":
        print("Failed:", st.get("error"))
        break

    print("Progress:", st)
    time.sleep(5)
```

### Example Running Response

```python
{
  "job_id": "b10425d6-c8eb-4ccb-8f93-a731bbe7d616",
  "status": "running",
  "found": 12,
  "percent complete": "41.87%",
  "runtime": "83.21s",
  "ETA": "115.42s",
  "GCPS": "8.12"
}
```

### Example Completed Response

```python
{
  "job_id": "b10425d6-c8eb-4ccb-8f93-a731bbe7d616",
  "status": "completed",
  "found": 42,
  "runtime": "198.57s",
  "total work": 250000,
  "total valid candidates": 42,
  "example valid candidates": [
    "010101010101",
    "001011010110"
  ]
}
```

### Example Failed Response

```python
{
  "job_id": "b10425d6-c8eb-4ccb-8f93-a731bbe7d616",
  "status": "failed",
  "error": {
    "message": "job failed"
  }
}
```

### `status()` Parameters

`status()` accepts:

- `job_id`
- `api_key`
- `example_count=1`

Rules for `example_count`:

- must be between `1` and `50`
- controls how many example candidates are returned
- applies when the job is completed

### Status Response Fields

| Field | Type | Description |
|---|---|---|
| `job_id` | `str` | Job UUID. |
| `status` | `str` | `running`, `completed`, or `failed`. |
| `found` | `int` | Number of valid candidates found so far, or total found if completed. |
| `percent complete` | `str` | Progress percentage while running. |
| `runtime` | `str` | Elapsed runtime. |
| `ETA` | `str` | Estimated time remaining while running. |
| `GCPS` | `str` | Giga-Combinations per second. |
| `total work` | `int` | Total work processed when completed. |
| `total valid candidates` | `int` | Final number of valid candidates. |
| `example valid candidates` | `str | list[str] | None` | Example candidates returned on completion. |
| `error` | `dict | None` | Failure details when status is `failed`. |

### Polling Recommendations

- sleep between polls, such as 5 seconds
- avoid tight loops
- increase `example_count` only when you need more sample candidates

## Retrieving Final Results

Once a job is complete, use `sgen.results(job_id, api_key)` to retrieve final output.

```python
import os
import time
import sgen

API_KEY = os.environ["SGEN_API_KEY"]

config = sgen.load_config("config.json")
job = sgen.quick_submit(config, api_key=API_KEY)
job_id = job["job_id"]

while True:
    st = sgen.status(job_id=job_id, api_key=API_KEY)

    if st is not None and st["status"] == "completed":
        break

    if st is not None and st["status"] == "failed":
        raise RuntimeError(f"Job failed: {st.get('error')}")

    time.sleep(5)

res = sgen.results(job_id=job_id, api_key=API_KEY)
print("Results:", res)
```

### Example Results Response

```python
{
  "job_id": "b10425d6-c8eb-4ccb-8f93-a731bbe7d616",
  "n": 15,
  "k": 4,
  "valid_candidates": [
    "010101010101",
    "001011010110"
  ]
}
```

### Recommended Results Pattern

The most reliable sequence is:

1. submit with `quick_submit()`
2. poll with `status()` until `completed`
3. fetch final output with `results()`

## Health and Connectivity

The SDK also includes convenience helpers:

### `health_check()`

Checks gateway health.

```python
import sgen

print(sgen.health_check())
```

### `round_trip_time()`

Measures health endpoint latency in milliseconds.

```python
import sgen

print(sgen.round_trip_time(), "ms")
```

## Job Helper Class

The SDK exports a `Job` class.

```python
from sgen import Job
```

If you keep the current SDK structure, `Job` can be used as a wrapper for polling and retrieval behavior around a known `job_id`.

## Return Value Conventions

A few current SDK behaviors are important to know:

- `load_config()` raises if the file is missing or invalid
- `quick_submit()` returns the gateway JSON response for a successful submission
- `status()` may return `None` when the job is not yet ready or not found
- `results()` may return `None` when results are not yet available
- unexpected HTTP errors are raised by the underlying request layer

## Troubleshooting

### `results()` returns `None`

The job is still running or results are not ready yet.

Recommended fix:

- continue polling `status()`
- wait for `status == "completed"`
- call `results()` again

### Job failed

If `status()` returns:

```python
{"status": "failed", "error": {...}}
```

inspect the error payload and validate your configuration.

### Config validation errors

At minimum, make sure:

- `n` is an integer
- `k` is an integer
- your JSON is well-formed

### Job not found or unauthorized

A `404` or missing result can mean:

- the `job_id` is wrong
- the API key does not have access to that job
- the job is not yet available through the endpoint being queried

## Example Repository README Section for GitHub

If you want a shorter top section for GitHub, you can use this summary:

> SGEN is a Python SDK for submitting bitmask-based graph search jobs, polling asynchronous execution, and retrieving valid candidate results from the SGEN gateway.

## License

MIT License