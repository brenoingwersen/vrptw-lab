"""API client for the dashboard

The API client is responsible for sending and receiving data from the frontend to the backend.
"""

from collections.abc import Callable
from typing import Any

import httpx
from loguru import logger

from dashboard.contracts import Dataset, RunRequest, RunResponse, SolutionResponse
from dashboard.settings import API_BASE_URL, REQUEST_TIMEOUT


def call_api[T](fn: Callable[[], T], *, context: str, fallback: T) -> T:
    """
    Call the given function and handle HTTP errors.
    """
    try:
        return fn()
    except httpx.HTTPError:
        logger.exception(context)
        return fallback


class APIClient:
    """
    API client for the dashboard defining the API endpoints
    """

    def __init__(self, base_url: str = API_BASE_URL) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=REQUEST_TIMEOUT)

    def close(self) -> None:
        self._client.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self._client.request(method, path, **kwargs)
        response.raise_for_status()
        return response.json()

    def list_datasets(self) -> list[Dataset]:
        """
        Request the list of available datasets from the backend
        """
        return self._request("GET", "/datasets")

    def list_runs(self) -> list[RunResponse]:
        """
        Request the list of available runs from the backend
        """
        return self._request("GET", "/runs")

    def get_run_solution(self, run_id: str) -> SolutionResponse:
        """
        Request the solution detail for a given ``run_id``.
        """
        logger.info(f"Getting the solution for run {run_id} from the backend.")
        return self._request("GET", f"/runs/{run_id}/solution")

    def create_run(self, payload: RunRequest) -> RunResponse:
        """
        Create a new run with the given payload with parameters.
        """
        logger.info(f"Creating a new run with the payload {payload}.")
        return self._request("POST", "/runs", json=payload)


api = APIClient()
