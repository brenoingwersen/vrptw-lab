"""
Dashboard layout.

The layout defines the *structure* of the dashboard by leaving *placeholders* for the contents to be displayed.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html

from dashboard.components.kpi_row import kpi_row
from dashboard.components.new_run_form import new_run_form
from dashboard.components.runs_table import runs_table
from dashboard.components.solution_summary_card import solution_row
from dashboard.contracts import Dataset, RunResponse, SolutionResponse
from dashboard.settings import REFRESH_INTERVAL_MS

# Initial values for the stores
DATASETS_STORE_DEFAULT: list[Dataset] = []
RUNS_STORE_DEFAULT: list[RunResponse] = []
SOLUTION_CACHE_STORE_DEFAULT: list[SolutionResponse] = []

_SECTION_MB = "mb-4"  # Margin bottom for each section


def _center_section(content, *, class_name: str = _SECTION_MB) -> dbc.Row:
    """
    Center the content in a row.
    """
    return dbc.Row(
        dbc.Col(content, xs=12, lg=10),
        justify="center",
        className=class_name,
    )


def build_layout() -> dbc.Container:
    """
    Return the layout of the dashboard.
    """

    children = [
        dcc.Location(id="url"),
        dcc.Store(id="datasets-store", data=DATASETS_STORE_DEFAULT),
        dcc.Store(id="runs-store", data=RUNS_STORE_DEFAULT),
        dcc.Store(id="selected-run-store"),
        dcc.Store(id="solution-cache-store", data=SOLUTION_CACHE_STORE_DEFAULT),
        dcc.Interval(
            id="refresh-interval", interval=REFRESH_INTERVAL_MS, n_intervals=0
        ),
    ]

    return dbc.Container(
        [
            *children,
            title_section(),
            new_run_section(),
            kpis_section(),
            runs_section(),
            solution_section(),
        ],
        fluid=True,
    )


def title_section() -> dbc.Row:
    return _center_section(
        html.A(
            "VRPTW Optimizer",
            href="/",
            className="navbar-brand fw-semibold fs-3",
        ),
        class_name="my-2 mb-4",
    )


def new_run_section() -> dbc.Row:
    return _center_section(new_run_form())


def kpis_section() -> dbc.Row:
    return _center_section(kpi_row())


def runs_section() -> dbc.Row:
    return _center_section(runs_table())


def solution_section() -> dbc.Row:
    return _center_section(solution_row())
