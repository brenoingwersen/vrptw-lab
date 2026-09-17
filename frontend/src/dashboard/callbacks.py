from dash import Input, Output, callback, State, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from dashboard.components import run_arcs_chart, dataset_instance_options
from dashboard.api_client import api


@callback(
    Output("runs-table", "rowData"),
    Input("refresh-interval", "n_intervals"),
)
def refresh_table(_n) -> list[dict]:
    try:
        runs = api.list_runs()
    except Exception as exc:
        return [], dbc.Alert(f"Failed to load runs: {exc}", color="danger")

    return runs


@callback(
    Output("run-arcs-chart", "figure"),
    Input("runs-table", "selectedRows"),
)
def update_selected_run_arcs(selected_rows: list[dict]) -> list[dict]:
    runs = api.list_runs()
    run_id = runs[0] if not selected_rows else selected_rows[0]["run_id"]
    return run_arcs_chart(run_id)


@callback(
    Output("new-run-dataset-instance-dropdown", "options"),
    Output("new-run-dataset-instance-dropdown", "value"),
    Input("new-run-dataset-name-dropdown", "value"),
    Input("new-run-dataset-instance-dropdown", "value"),
    State("datasets-store", "data"),
)
def filter_instances(selected_name, selected_instance, datasets):
    options = dataset_instance_options(datasets or [], selected_name)
    valid_values = {opt["value"] for opt in options}
    if selected_instance not in valid_values:
        selected_instance = None
    return options, selected_instance


@callback(
    Output("new-run-feedback", "children"),
    Output("runs-table", "rowData", allow_duplicate=True),  # refresh table
    Input("new-run-button", "n_clicks"),
    State("new-run-dataset-name-dropdown", "value"),
    State("new-run-dataset-instance-dropdown", "value"),
    State("new-run-max-trucks", "value"),
    State("new-run-truck-capacity", "value"),
    State("new-run-max-time", "value"),
    State("new-run-random-seed", "value"),
    prevent_initial_call=True,
)
def create_new_run(
    n_clicks, name, instance, max_trucks, truck_capacity, max_time, random_seed
):
    if not n_clicks:
        raise PreventUpdate
    if not name or not instance:
        return dbc.Alert(
            "Select both dataset and instance.", color="warning"
        ), no_update
    payload = {
        "name": name,
        "instance": instance,
        "max_trucks": int(max_trucks),
        "truck_capacity": int(truck_capacity),
    }
    if max_time is not None and max_time != "":
        payload["max_time_in_seconds"] = int(max_time)
    if random_seed is not None and random_seed != "":
        payload["random_seed"] = int(random_seed)
    try:
        run = api.create_run(payload)
        alert = dbc.Alert(f"Run {run['run_id']} queued.", color="success")
        return alert, api.list_runs()
    except Exception as exc:
        return dbc.Alert(f"Failed to create run: {exc}", color="danger"), no_update
