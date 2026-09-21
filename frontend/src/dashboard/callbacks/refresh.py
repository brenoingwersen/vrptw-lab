from dash import Input, Output, State, callback, no_update

from dashboard.api_client import api, call_api
from dashboard.contracts import Dataset, RunResponse


@callback(
    Output("datasets-store", "data"),
    Input("url", "pathname"),
)
def load_datasets(_) -> list[Dataset]:
    """
    Callback to load the available datasets on the first load
    """
    return call_api(
        api.list_datasets,
        context="Failed to load datasets",
        fallback=[],
    )


@callback(
    Output("runs-store", "data"),
    Input("refresh-interval", "n_intervals"),
    State("runs-store", "data"),
)
def update_runs(
    _n_intervals: int, _previous_runs: list[RunResponse]
) -> list[RunResponse]:
    """
    Callback to refresh the runs store every interval
    """
    return call_api(
        api.list_runs,
        context="Failed to refresh runs",
        fallback=no_update,
    )
