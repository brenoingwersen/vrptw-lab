from dash import Input, Output, State, callback

from dashboard.api_client import APIClient
from dashboard.contracts import RunResponse, SolutionResponse
from dashboard.settings import MAX_CACHED_SOLUTIONS

api = APIClient()


def _get_cached_solution(
    solutions: list[SolutionResponse], run_id: str
) -> SolutionResponse | None:
    """
    Get a cached solution for a given run ID
    """
    for solution in solutions:
        if solution.get("run", {}).get("run_id") == run_id:
            return solution
    return None


def _cache_solution(
    solutions: list[SolutionResponse], run_id: str, solution: SolutionResponse
) -> list[SolutionResponse]:
    """
    FIFO cache: first in first out
    """
    solutions_filtered = [
        item for item in solutions if item.get("run", {}).get("run_id") != run_id
    ]

    solutions_filtered.append(solution)

    return solutions_filtered[-MAX_CACHED_SOLUTIONS:]


@callback(
    Output("runs-table", "rowData"),
    Input("runs-store", "data"),
)
def update_runs_table(runs: list[RunResponse]) -> list[RunResponse]:
    """
    Callback to update the runs table when the runs store is updated
    """
    return runs


@callback(
    Output("solution-cache-store", "data"),
    Output("selected-run-store", "data"),
    Input("runs-table", "selectedRows"),
    State("solution-cache-store", "data"),
)
def select_solution(
    selected_rows: list[RunResponse], solutions_cache: list[SolutionResponse]
) -> tuple[list[RunResponse], RunResponse | None]:
    """
    Callback to select a solution when a run is selected
    """
    if len(selected_rows) == 0:
        return solutions_cache, None

    selected_run = selected_rows[0]
    run_id = selected_run.get("run_id")
    if run_id is None:
        return solutions_cache, None

    # Get the cached solution or fetch it from the backend
    cached_solution = _get_cached_solution(
        solutions_cache, run_id
    ) or api.get_run_solution(run_id)

    # Cache the solution
    solutions_cache = _cache_solution(solutions_cache, run_id, cached_solution)

    return solutions_cache, selected_run
