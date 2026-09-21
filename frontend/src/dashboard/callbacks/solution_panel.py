import plotly.graph_objects as go
from dash import Input, Output, State, callback

from dashboard.contracts import RunResponse, SolutionResponse
from dashboard.plot import build_solution_chart

_DEFAULT_PLACEHOLDER = "N/A"
_DEFAULT_FIGURE = build_solution_chart(None)
_DEFAULT_RETURN_VALUES = (
    "No selected run",
    *[_DEFAULT_PLACEHOLDER] * 7,
    _DEFAULT_FIGURE,
)


def _format_value(value: object, decimals: int = 0) -> str:
    if value is None or value == "":
        return _DEFAULT_PLACEHOLDER

    if isinstance(value, float):
        return f"{value:,.{decimals}f}"

    if isinstance(value, int):
        return f"{value:,}"

    return str(value)


@callback(
    Output("selected-run-id", "children"),
    Output("total-runtime-label", "children"),
    Output("total-trucks-label", "children"),
    Output("total-distance-label", "children"),
    Output("max-trucks-label", "children"),
    Output("truck-capacity-label", "children"),
    Output("max-time-label", "children"),
    Output("random-seed-label", "children"),
    Output("solution-chart", "figure"),
    Input("selected-run-store", "data"),
    State("solution-cache-store", "data"),
)
def update_solution_panel(
    selected_run: RunResponse | None, solution_cache: list[SolutionResponse]
) -> tuple[str, str, str, str, str, str, str, str, go.Figure]:
    if selected_run is None:
        return _DEFAULT_RETURN_VALUES

    run_id = selected_run.get("run_id")
    if run_id is None:
        return _DEFAULT_RETURN_VALUES

    solution = next(
        (s for s in solution_cache if s.get("run").get("run_id") == run_id),
        None,
    )
    if solution is None:
        return _DEFAULT_RETURN_VALUES

    return (
        f"Run: {run_id[:18]}..." if run_id != _DEFAULT_PLACEHOLDER else run_id,
        f"Total runtime (s): {_format_value(selected_run.get('runtime_seconds'), decimals=3)}",
        _format_value(selected_run.get("total_trucks")),
        _format_value(selected_run.get("total_distance"), decimals=2),
        _format_value(selected_run.get("max_trucks")),
        _format_value(selected_run.get("truck_capacity")),
        _format_value(selected_run.get("max_time_in_seconds"), decimals=3),
        _format_value(selected_run.get("random_seed")),
        build_solution_chart(solution),
    )
