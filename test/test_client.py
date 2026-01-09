import unittest
from unittest.mock import patch
from sgen import client

class TestSubmitJob(unittest.TestCase):

    @patch("sgen.client.requests.post")
    def test_submit_job(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "job_id": "test-123"
        }

        config = {"task": "test"}
        job = client.submit_job(config, api_key="fake-key")

        self.assertEqual(job.job_id, "test-123")
        self.assertEqual(job.api_key, "fake-key")
        mock_post.assert_called_once_with(
            "https://your-cloudflare-endpoint.com/start-job",
            json=config,
            headers={"Authorization": "Bearer fake-key"}
        )

if __name__ == "__main__":
    unittest.main()
