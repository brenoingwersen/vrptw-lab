import httpx
from dashboard.settings import API_BASE_URL, REQUEST_TIMEOUT


class APIClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url

    def list_datasets(self) -> list[dict]:
        with httpx.Client(base_url=self.base_url, timeout=REQUEST_TIMEOUT) as client:
            response = client.get("/dashboard/datasets/")
            response.raise_for_status()
            return response.json()

    def list_runs(self, limit: int | None = None) -> list[dict]:
        """
        List all runs from the backend.
        """
        params = {"limit": limit} if limit is not None else {}
        with httpx.Client(base_url=self.base_url, timeout=REQUEST_TIMEOUT) as client:
            response = client.get("/dashboard/runs/", params=params)
            response.raise_for_status()
            return response.json()

    def get_run_dashboard_arcs(self, run_id: str) -> list[dict]:
        with httpx.Client(base_url=self.base_url, timeout=REQUEST_TIMEOUT) as client:
            response = client.get(f"/dashboard/runs/{run_id}/arcs/")
            response.raise_for_status()
            return response.json()

    def create_run(self, payload: dict) -> dict:
        with httpx.Client(base_url=self.base_url, timeout=REQUEST_TIMEOUT) as client:
            response = client.post("/runs/", json=payload)
            response.raise_for_status()
            return response.json()


api = APIClient()
