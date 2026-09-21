import dash_bootstrap_components as dbc
from dash import dcc, html

from dashboard.plot import build_solution_chart


def solution_summary_card() -> dbc.Card:
    return dbc.Card(
        [
            dbc.CardHeader(
                "No run selected",
                className="fw-bold fs-5 pb-2",
                id="selected-run-id",
            ),
            dbc.Row(
                html.P(
                    "Total runtime (s):",
                    id="total-runtime-label",
                    className="fst-italic",
                ),
                className="mx-2 mt-2",
            ),
            dbc.Row(
                [
                    dbc.Label("Objective values", className="fw-semibold fs-6"),
                    dbc.Col(
                        [
                            dbc.Row(dbc.Label("Total trucks")),
                            dbc.Row(
                                dbc.Label(
                                    "N/A",
                                    id="total-trucks-label",
                                    className="fw-semibold",
                                )
                            ),
                        ],
                    ),
                    dbc.Col(
                        [
                            dbc.Row(dbc.Label("Total distance")),
                            dbc.Row(
                                dbc.Label(
                                    "N/A",
                                    id="total-distance-label",
                                    className="fw-semibold",
                                )
                            ),
                        ]
                    ),
                ],
                className="mx-2 mb-2",
            ),
            dbc.Row(
                [
                    dbc.Label("Constraints", className="fw-semibold fs-6"),
                    dbc.Col(
                        [
                            dbc.Row(dbc.Label("Max trucks")),
                            dbc.Row(
                                dbc.Label(
                                    "N/A",
                                    id="max-trucks-label",
                                    className="fw-semibold",
                                )
                            ),
                        ],
                    ),
                    dbc.Col(
                        [
                            dbc.Row(dbc.Label("Truck capacity")),
                            dbc.Row(
                                dbc.Label(
                                    "N/A",
                                    id="truck-capacity-label",
                                    className="fw-semibold",
                                )
                            ),
                        ]
                    ),
                ],
                className="mx-2 mb-2",
            ),
            dbc.Row(
                [
                    dbc.Label("Solver parameters", className="fw-semibold fs-6"),
                    dbc.Col(
                        [
                            dbc.Row(dbc.Label("Max time (s)")),
                            dbc.Row(
                                dbc.Label(
                                    "N/A",
                                    id="max-time-label",
                                    className="fw-semibold",
                                )
                            ),
                        ],
                    ),
                    dbc.Col(
                        [
                            dbc.Row(dbc.Label("Random seed")),
                            dbc.Row(
                                dbc.Label(
                                    "N/A",
                                    id="random-seed-label",
                                    className="fw-semibold",
                                )
                            ),
                        ]
                    ),
                ],
                className="mx-2 mb-2",
            ),
        ],
        className="h-100 shadow-sm my-2",
    )


def solution_row() -> dbc.Row:
    return (
        dbc.Row(
            [
                dbc.Col(solution_summary_card(), xs=12, md=4),
                dbc.Col(
                    html.Div(
                        dcc.Graph(
                            id="solution-chart",
                            figure=build_solution_chart(None),
                        ),
                        className="border shadow-sm rounded bg-white h-100 my-2",
                    ),
                    xs=12,
                    md=8,
                ),
            ],
            className="g-3 align-items-stretch",
        ),
    )
