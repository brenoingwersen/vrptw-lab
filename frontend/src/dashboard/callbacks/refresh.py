from dash import Input, Output, callback

from dashboard.api_client import APIClient
from dashboard.contracts import Dataset, RunResponse

api = APIClient()


@callback(
    Output("datasets-store", "data"),
    Input("url", "pathname"),
)
def load_datasets(_) -> list[Dataset]:
    """
    Callback to load the available datasets on the first load
    """
    return api.list_datasets()


@callback(Output("runs-store", "data"), Input("refresh-interval", "n_intervals"))
def update_runs(_n_intervals: int) -> list[RunResponse]:
    """
    Callback to refresh the runs store every interval
    """
    return api.list_runs()
