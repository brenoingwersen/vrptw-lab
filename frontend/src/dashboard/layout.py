import dash_bootstrap_components as dbc
from dash import html, dcc

from dashboard.components import (
    runs_table,
    run_arcs_chart,
    total_runs,
    total_queued_runs,
    total_running_runs,
    total_failed_runs,
    dataset_name_options,
)

from dashboard.api_client import api


def build_layout() -> dbc.Container:
    """
    Build the layout of the dashboard.

    The layout defines the placeholders only through IDs, not data.
    """

    interval = dcc.Interval(id="refresh-interval", interval=15_000, n_intervals=0)

    datasets = api.list_datasets()

    new_run_form_section = dbc.Row(
        dbc.Col(
            [
                dcc.Store(id="datasets-store", data=datasets),
                dbc.Label("Create a new run:", className="fw-semibold mb-2"),
                # Row 1: dataset selection
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label(
                                    "Dataset", html_for="new-run-dataset-name-dropdown"
                                ),
                                dcc.Dropdown(
                                    id="new-run-dataset-name-dropdown",
                                    options=dataset_name_options(datasets),
                                    placeholder="Select dataset...",
                                    clearable=True,
                                ),
                            ],
                            md=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Label(
                                    "Instance",
                                    html_for="new-run-dataset-instance-dropdown",
                                ),
                                dcc.Dropdown(
                                    id="new-run-dataset-instance-dropdown",
                                    options=[],  # filled by callback
                                    placeholder="Select instance...",
                                    clearable=True,
                                ),
                            ],
                            md=6,
                        ),
                    ],
                    className="mb-3",
                ),
                # Row 2: solver parameters
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("Max trucks", html_for="new-run-max-trucks"),
                                dbc.Input(
                                    id="new-run-max-trucks",
                                    type="number",
                                    min=1,
                                    value=20,
                                ),
                            ],
                            md=3,
                        ),
                        dbc.Col(
                            [
                                dbc.Label(
                                    "Truck capacity", html_for="new-run-truck-capacity"
                                ),
                                dbc.Input(
                                    id="new-run-truck-capacity",
                                    type="number",
                                    min=1,
                                    value=200,
                                ),
                            ],
                            md=3,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Max time (s)", html_for="new-run-max-time"),
                                dbc.Input(
                                    id="new-run-max-time",
                                    type="number",
                                    min=1,
                                    value=60,
                                ),
                            ],
                            md=3,
                        ),
                        dbc.Col(
                            [
                                dbc.Label(
                                    "Random seed", html_for="new-run-random-seed"
                                ),
                                dbc.Input(
                                    id="new-run-random-seed",
                                    type="number",
                                    placeholder="optional",
                                ),
                            ],
                            md=3,
                        ),
                    ],
                    className="mb-3",
                ),
                # Row 3: submit + feedback
                dbc.Row(
                    [
                        dbc.Button(
                            "Create run",
                            id="new-run-button",
                            color="primary",
                        ),
                        html.Div(id="new-run-feedback", className="mt-2"),
                    ],
                    # style={"padding-right": "50px"},
                    className="px-3",
                ),
            ],
            width=10,
        ),
        justify="center",
        className="mb-4",
    )

    title_section = dbc.Row(
        [
            dbc.Col(
                html.H1(
                    "VRPTW Dashboard",
                    className="text-secondary text-center fw-bold display-5 my-4 p-3 bg-light rounded shadow-sm",
                ),
                width=12,
            )
        ]
    )

    kpis = [
        {
            "label": "Total runs:",
            "value": total_runs(),
            "id": "total-runs",
            "color": "primary",
        },
        {
            "label": "Queued:",
            "value": total_queued_runs(),
            "id": "total-queued-runs",
            "color": "warning",
        },
        {
            "label": "Running:",
            "value": total_running_runs(),
            "id": "total-running-runs",
            "color": "info",
        },
        {
            "label": "Failed:",
            "value": total_failed_runs(),
            "id": "total-failed-runs",
            "color": "danger",
        },
    ]

    kpis_section = dbc.Row(
        dbc.Col(
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                html.Div(
                                    [
                                        html.Div(
                                            className=f"border-start border-3 border-{kpi['color']}",
                                            style={
                                                "height": "3em",
                                                "padding-left": "1em",
                                            },
                                        ),
                                        html.Span(
                                            kpi["label"],
                                            className="fw-semibold me-2",
                                        ),
                                        html.Span(
                                            kpi["value"],
                                            id=kpi["id"],
                                            className="fs-4 fw-bold",
                                        ),
                                    ],
                                    className="d-flex align-items-center",
                                ),
                            ),
                            className="border-start shadow-sm",
                        ),
                        xs=12,
                        sm=6,
                        lg=3,
                    )
                    for kpi in kpis
                ],
                className="g-3",
                justify="center",
            ),
            width=10,
            className="mb-4",
        ),
        justify="center",
    )

    runs_table_section = dbc.Row(
        dbc.Col(
            runs_table(),
            width=10,
        ),
        justify="center",  # Center inside the row
        className="mb-4",
    )

    run_arcs_chart_section = dbc.Row(
        dbc.Col(
            dcc.Graph(
                id="run-arcs-chart",
                figure=run_arcs_chart(api.list_runs()[0]["run_id"]),
                className="border rounded-2 shadow-sm",
            ),
            width=10,
        ),
        justify="center",
        className="mb-4",
    )

    return dbc.Container(
        [
            interval,
            title_section,
            new_run_form_section,
            kpis_section,
            runs_table_section,
            run_arcs_chart_section,
        ],
        fluid=True,
    )
