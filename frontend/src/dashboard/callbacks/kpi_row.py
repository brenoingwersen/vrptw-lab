from enum import StrEnum

from dash import Input, Output, callback

from dashboard.contracts import RunResponse


class RunStatus(StrEnum):
    queued = "queued"
    running = "running"
    failed = "failed"
    completed = "completed"


def _count_runs_by_status(runs: list[RunResponse], status: str | None = None) -> int:
    """
    Count the number of runs by status.
    """
    if status is None:
        return len(runs)

    try:
        _status = RunStatus(status)
    except ValueError:
        raise ValueError(f"Invalid run status: {status}")

    return len([r for r in runs if r["status"] == _status.value])


@callback(
    Output("kpi-total-runs", "children"),
    Output("kpi-total-queued-runs", "children"),
    Output("kpi-total-running-runs", "children"),
    Output("kpi-total-failed-runs", "children"),
    Input("runs-store", "data"),
)
def update_kpi_row(runs: list[RunResponse]) -> tuple[str, str, str, str]:
    return (
        str(_count_runs_by_status(runs)),
        str(_count_runs_by_status(runs, RunStatus.queued)),
        str(_count_runs_by_status(runs, RunStatus.running)),
        str(_count_runs_by_status(runs, RunStatus.failed)),
    )
