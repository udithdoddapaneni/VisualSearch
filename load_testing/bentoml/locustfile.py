"""Load Testing with Locust for BentoML."""

import json
import secrets
from pathlib import Path
from typing import ClassVar

import yaml
from locust import HttpUser, between, task

# Load configuration from YAML file
with Path("..", "locust.yaml").open() as config_file:
    config = yaml.safe_load(config_file)

# Get FastAPI host and port from the YAML config
fastapi_config = config.get("bentoml", {})
host = fastapi_config.get("host", "localhost")
port = fastapi_config.get("port", 3000)


RESPONSE_ACCEPTED = 202
RESPONSE_OK = 200
ACCEPTED_TIME = 5


class QueryUser(HttpUser):
    """Locust user class for querying FastAPI endpoints."""

    # Set the host from the YAML file
    host = f"http://{host}:{port}"
    # Wait time between tasks
    wait_time = between(1, 3)

    texts: ClassVar[list] = ["train", "cat", "dog", "fish", "children"]
    types: ClassVar[list] = ["image", "video"]

    @task(2)
    def query_endpoint(self) -> None:
        """Task to query the BentoML /query endpoint."""
        # Randomly choose values for payload
        payload = {
            "text": secrets.choice(self.texts),
            "type": secrets.choice(self.types),
            "n": secrets.randbelow(100) + 1,
        }
        # Headers (ensure you have the proper content-type if needed)
        headers = {"Content-Type": "application/json"}

        # Send POST request to /query endpoint
        with self.client.post("/query", json=payload, headers=headers, catch_response=True) as response:
            if response.status_code == RESPONSE_ACCEPTED:
                response.raise_for_status()
                result_line = f"SUCCESS: Request: {json.dumps(payload)} | Response: {response.text}\n"
            else:
                response.failure(f"Status code: {response.status_code}")  # type: ignore  # noqa: PGH003
                result_line = f"FAILURE: Request: {json.dumps(payload)} | Response: {response.text}\n"

            # Append the result to a file
            with Path("results.txt").open("a") as result_file:
                result_file.write(result_line)

    @task(1)
    def get_all_images(self) -> None:
        """Task to query the BentoML /all_images endpoint."""
        headers = {"Content-Type": "application/json"}
        payload = {}
        with self.client.post("/all_images", json=payload, headers=headers, catch_response=True) as response:
            # Check if request took more than 4 seconds
            if response.elapsed.total_seconds() > ACCEPTED_TIME:
                response.failure(f"Request took too long: {response.elapsed.total_seconds()} secs")  # type: ignore  # noqa: PGH003
            elif response.status_code != RESPONSE_OK:
                response.failure(f"Unexpected status code: {response.status_code}")  # type: ignore  # noqa: PGH003
            else:
                response.success()  # type: ignore  # noqa: PGH003

    @task(1)
    def get_all_videos(self) -> None:
        """Task to query the BentoML /all_videos endpoint."""
        headers = {"Content-Type": "application/json"}
        payload = {}
        with self.client.post("/all_videos", json=payload, headers=headers, catch_response=True) as response:
            # Check if request took more than 4 seconds
            if response.elapsed.total_seconds() > ACCEPTED_TIME:
                response.failure(f"Request took too long: {response.elapsed.total_seconds()} secs")  # type: ignore  # noqa: PGH003
            elif response.status_code != RESPONSE_OK:
                response.failure(f"Unexpected status code: {response.status_code}")  # type: ignore  # noqa: PGH003
            else:
                response.success()  # type: ignore  # noqa: PGH003
