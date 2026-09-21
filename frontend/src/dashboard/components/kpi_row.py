import dash_bootstrap_components as dbc
from dash import html


def kpi_card(title: str, id: str, color: str = "success") -> dbc.Col:
    return dbc.Col(
        dbc.Card(
            html.Div(
                [
                    html.P(title, className="mb-1"),
                    dbc.Label("N/A", className="fw-bold fs-5 m-0", id=id),
                ],
                className=f"border-{color} border-start border-5 p-2",
            )
        ),
        xs=12,
        sm=6,
        lg=3,
    )


def kpi_row() -> dbc.Row:
    kpis = [
        {"title": "Total runs", "id": "kpi-total-runs", "color": "success"},
        {"title": "Total queued runs", "id": "kpi-total-queued-runs", "color": "info"},
        {
            "title": "Total running runs",
            "id": "kpi-total-running-runs",
            "color": "warning",
        },
        {
            "title": "Total failed runs",
            "id": "kpi-total-failed-runs",
            "color": "danger",
        },
    ]

    return dbc.Row([kpi_card(**kpi) for kpi in kpis], className="g-3")
