from typing import TypedDict

import dash_bootstrap_components as dbc
import httpx
from dash import Input, Output, State, callback
from loguru import logger

from dashboard.api_client import APIClient
from dashboard.contracts import Dataset, RunRequest

api = APIClient()


_ALERT_CLASSNAME = "mb-0 w-100"


class DropdownOption(TypedDict):
    """
    Type for dropdown options
    """

    label: str
    value: str


@callback(
    Output("dataset-dropdown", "options"),
    Input("datasets-store", "data"),
)
def update_dataset_dropdown(datasets: list[Dataset]) -> list[DropdownOption]:
    return [
        {
            "label": f"{d['name']}/{d['instance']}",
            "value": f"{d['name']}/{d['instance']}",
        }
        for d in sorted(datasets, key=lambda x: f"{x['name']}/{x['instance']}")
    ]


@callback(
    Output("new-run-feedback", "children"),
    Input("new-run-button", "n_clicks"),
    State("dataset-dropdown", "value"),
    State("max-trucks-input", "value"),
    State("truck-capacity-input", "value"),
    State("max-time-input", "value"),
    State("random-seed-input", "value"),
    prevent_initial_call=True,
)
def create_new_run(
    n_clicks: int,
    dataset: str | None,
    max_trucks: int,
    truck_capacity: int,
    max_time_in_seconds: int | None,
    random_seed: int | None,
) -> dbc.Alert:
    """
    Callback to post a new run to the backend.
    """
    if not dataset:
        return dbc.Alert(
            "Select a dataset to create a new run.",
            color="warning",
            className=_ALERT_CLASSNAME,
        )

    name, instance = dataset.split("/", maxsplit=1)

    payload: RunRequest = {
        "name": name,
        "instance": instance,
        "max_trucks": max_trucks,
        "truck_capacity": truck_capacity,
        "max_time_in_seconds": max_time_in_seconds,
        "random_seed": random_seed,
    }

    try:
        response = api.create_run(payload)

    except httpx.HTTPError:
        logger.exception(
            "Failed to create run for dataset {}/{}",
            name,
            instance,
        )
        return dbc.Alert(
            "The backend could not create the run.",
            color="danger",
            className=_ALERT_CLASSNAME,
        )

    return dbc.Alert(
        f"Run {response['run_id']} created successfully.",
        color="success",
        className=_ALERT_CLASSNAME,
    )
