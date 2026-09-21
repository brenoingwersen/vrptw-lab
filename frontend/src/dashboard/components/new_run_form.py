import dash_bootstrap_components as dbc
from dash import dcc, html


def _dataset_fields() -> dbc.Col:
    return dbc.Col(
        [
            dbc.Label(
                "Select dataset",
                html_for="dataset-dropdown",
                className="fw-semibold mb-2",
            ),
            dcc.Dropdown(
                id="dataset-dropdown",
                options=[],
                placeholder="Select dataset...",
            ),
        ],
        xs=12,
        md=4,
    )


def _constraints_fields() -> dbc.Col:
    max_trucks_input = dbc.Col(
        [
            dbc.Label(
                "Max trucks",
                html_for="max-trucks-input",
                className="fw-semibold",
            ),
            dbc.Input(
                id="max-trucks-input",
                type="number",
                min=1,
                value=20,
            ),
        ],
        xs=12,
        md=6,
    )

    truck_capacity_input = dbc.Col(
        [
            dbc.Label(
                "Truck capacity",
                html_for="truck-capacity-input",
                className="fw-semibold",
            ),
            dbc.Input(
                id="truck-capacity-input",
                type="number",
                min=1,
                value=200,
            ),
        ],
        xs=12,
        md=6,
    )

    max_time_in_seconds_input = dbc.Col(
        [
            dbc.Label(
                "Time limit (s)",
                html_for="max-time-input",
                className="fw-semibold",
            ),
            dbc.Input(
                id="max-time-input",
                type="number",
                min=1,
                value=60,
            ),
        ],
        xs=12,
        md=6,
    )

    random_seed_input = dbc.Col(
        [
            dbc.Label(
                "Random seed",
                html_for="random-seed-input",
                className="fw-semibold",
            ),
            dbc.Input(
                id="random-seed-input",
                type="number",
                placeholder="optional",
            ),
        ],
        xs=12,
        md=6,
    )

    return dbc.Col(
        [
            dbc.Row(
                [max_trucks_input, truck_capacity_input],
                className="g-3 mb-2",
            ),
            dbc.Row(
                [max_time_in_seconds_input, random_seed_input],
                className="g-3 mb-2",
            ),
            html.Div(
                [
                    html.Div(
                        id="new-run-feedback",
                        className="flex-grow-1",
                        style={"minWidth": 0},  # lets the alert shrink/wrap on mobile
                    ),
                    dbc.Button(
                        "Start run",
                        color="primary",
                        id="new-run-button",
                        className="flex-shrink-0 align-self-center text-nowrap py-3",
                    ),
                ],
                className="d-flex flex-nowrap align-items-center gap-2 mt-2",
            ),
        ],
        xs=12,
        md=8,
    )


def new_run_form() -> dbc.Card:
    return dbc.Card(
        [
            dbc.CardHeader("Create new run:", className="fw-semibold fs-5"),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Label("Dataset", className="fw-semibold fs-5"),
                                xs=12,
                                md=4,
                            ),
                            dbc.Col(
                                dbc.Label("Constraints", className="fw-semibold fs-5"),
                                xs=12,
                                md=8,
                            ),
                        ],
                        className="g-3 mb-2",
                    ),
                    dbc.Row(
                        [_dataset_fields(), _constraints_fields()],
                        className="g-4 align-items-stretch",
                    ),
                ]
            ),
        ],
        className="shadow-sm",
    )
