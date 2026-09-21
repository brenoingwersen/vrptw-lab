"""API client for the dashboard

The API client is responsible for sending and receiving data from the frontend to the backend.
"""

import httpx
from loguru import logger

from dashboard.contracts import Dataset, RunRequest, RunResponse, SolutionResponse
from dashboard.settings import API_BASE_URL, REQUEST_TIMEOUT


class APIClient:
    """
    API client for the dashboard
    """

    def __init__(self, base_url: str = API_BASE_URL) -> None:
        self.base_url = base_url

    def list_datasets(self) -> list[Dataset]:
        """
        Request the list of available datasets from the backend
        """
        with httpx.Client(base_url=self.base_url, timeout=REQUEST_TIMEOUT) as client:
            response = client.get("/datasets")
            response.raise_for_status()
            return response.json()

    def list_runs(self) -> list[RunResponse]:
        """
        Request the list of available runs from the backend
        """
        with httpx.Client(base_url=self.base_url, timeout=REQUEST_TIMEOUT) as client:
            response = client.get("/runs")
            response.raise_for_status()
            return response.json()

    def get_run_solution(self, run_id: str) -> SolutionResponse:
        """
        Request the solution detail for a given ``run_id``.
        """
        logger.info(f"Getting the solution for run {run_id} from the backend.")
        with httpx.Client(base_url=self.base_url, timeout=REQUEST_TIMEOUT) as client:
            response = client.get(f"/runs/{run_id}/solution")
            response.raise_for_status()
            return response.json()

    def create_run(self, payload: RunRequest) -> RunResponse:
        """
        Create a new run with the given payload with parameters.
        """
        logger.info(f"Creating a new run with the payload {payload}.")
        with httpx.Client(base_url=self.base_url, timeout=REQUEST_TIMEOUT) as client:
            response = client.post("/runs", json=payload)
            response.raise_for_status()
            return response.json()
