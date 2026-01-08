from sgen import client

def test_submit():
    config = {"example": "value"}
    job = client.submit_job(config, api_key="your-token")
    print(job.get_status())
