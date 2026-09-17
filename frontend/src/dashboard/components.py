import dash_ag_grid as dag
from dash import dcc
import plotly.graph_objects as go
from dashboard.api_client import api
import plotly.express as px


def dataset_name_options(datasets: list[dict]) -> list[dict]:
    names = sorted({d["name"] for d in datasets})
    return [{"label": n, "value": n} for n in names]


def dataset_instance_options(datasets: list[dict], name: str | None) -> list[dict]:
    if not name:
        return []
    instances = sorted(d["instance"] for d in datasets if d["name"] == name)
    return [{"label": i, "value": i} for i in instances]


def total_runs() -> str:
    """
    Return the total number of runs.
    """
    return str(len(api.list_runs()))


def total_queued_runs() -> str:
    """
    Return the total number of queued runs.
    """
    return str(len([r for r in api.list_runs() if r["status"] == "queued"]))


def total_running_runs() -> str:
    """
    Return the total number of running runs.
    """
    return str(len([r for r in api.list_runs() if r["status"] == "running"]))


def total_failed_runs() -> str:
    """
    Return the total number of failed runs.
    """
    return str(len([r for r in api.list_runs() if r["status"] == "failed"]))


def runs_table() -> dag.AgGrid:
    """
    Build the runs table component.
    """
    column_defs = [
        {
            "field": "run_id",
            "filter": "agTextColumnFilter",
            "filterParams": {
                "buttons": ["reset", "apply"],
            },
        },
        {
            "field": "name",
            "headerName": "Dataset",
            "filter": "agTextColumnFilter",
            "filterParams": {
                "buttons": ["reset", "apply"],
            },
        },
        {
            "field": "instance",
            "filter": "agTextColumnFilter",
            "filterParams": {
                "buttons": ["reset", "apply"],
            },
        },
        {
            "field": "created_at",
            "filter": "agTextColumnFilter",
            "filterParams": {
                "buttons": ["reset", "apply"],
            },
        },
        {
            "field": "finished_at",
            "filter": "agTextColumnFilter",
            "filterParams": {
                "buttons": ["reset", "apply"],
            },
        },
        {
            "field": "status",
            "filter": "agTextColumnFilter",
            "filterParams": {
                "buttons": ["reset", "apply"],
            },
            "cellRenderer": "StatusBadge",
            "cellRendererParams": {"className": "badge bg-primary"},
        },
    ]
    runs = api.list_runs()
    return dag.AgGrid(
        id="runs-table",
        rowData=runs,
        columnDefs=column_defs,
        columnSize="sizeToFit",
        defaultColDef={"flex": 1, "filter": True},
        dashGridOptions={
            "animateRows": False,
            "rowSelection": {"mode": "singleRow", "enableClickSelection": True},
        },
        selectedRows=[runs[0]],
    )


def run_arcs_chart(run_id: str) -> go.Figure:
    """Build the run arcs chart component."""

    dashboard_arcs = api.get_run_dashboard_arcs(run_id)

    arcs_by_truck: dict[int, list[dict]] = {}

    for arc in dashboard_arcs:
        arcs_by_truck.setdefault(arc["truck_id"], []).append(arc)

    colors = px.colors.qualitative.Plotly

    traces = []

    for index, (truck_id, arcs) in enumerate(arcs_by_truck.items()):
        color = colors[index % len(colors)]

        edge_x: list[float | None] = []
        edge_y: list[float | None] = []
        node_x: list[float] = []
        node_y: list[float] = []

        for arc in arcs:
            customer_from = arc["customer_from"]
            customer_to = arc["customer_to"]

            x0, y0 = customer_from["xcoord"], customer_from["ycoord"]
            x1, y1 = customer_to["xcoord"], customer_to["ycoord"]

            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

            node_x.append(x0)
            node_y.append(y0)

        traces.append(
            go.Scatter(
                x=edge_x,
                y=edge_y,
                mode="lines+markers",
                line={"width": 1, "color": "#888"},
                marker={"size": 8, "color": color},
                name=f"Truck {truck_id}",
            )
        )

    fig = go.Figure(data=traces)

    fig.update_layout(
        title=f"Run {run_id}",
        xaxis_title="X",
        yaxis_title="Y",
        yaxis={"scaleanchor": "x", "scaleratio": 1},
        plot_bgcolor="white",
    )

    return fig
