from collections.abc import Generator

import plotly.express as px
import plotly.graph_objects as go

from dashboard.contracts import Arc, Customer, SolutionResponse

colors = px.colors.qualitative.Plotly


def _iter_arcs_by_truck(
    arcs: list[Arc],
) -> Generator[tuple[str, list[Arc]]]:
    arcs_by_truck = {}
    for arc in arcs:
        arcs_by_truck.setdefault(arc["truck_id"], []).append(arc)

    yield from arcs_by_truck.items()


def _collect_customers(arcs: list[Arc]) -> dict[int, Customer]:
    customers: dict[int, Customer] = {}
    for arc in arcs:
        for key in ("cust_from", "cust_to"):
            customer = arc[key]
            customers[customer["cust_no"]] = customer
    return customers


def _is_depot(customer: Customer) -> bool:
    return customer["cust_no"] == 1


def _stops_for_truck(truck_arcs: list[Arc]) -> list[Customer]:
    stops: dict[int, Customer] = {}
    for arc in truck_arcs:
        for key in ("cust_from", "cust_to"):
            customer = arc[key]
            if not _is_depot(customer):
                stops[customer["cust_no"]] = customer
    return list(stops.values())


def _build_chart_traces(solution: SolutionResponse) -> list[go.Scatter]:
    arcs = solution.get("arcs", [])
    if len(arcs) == 0:
        raise ValueError("No arcs in solution")

    traces: list[go.Scatter] = []

    # 1) Route lines and customer markers (one pair per truck)
    for truck_id, truck_arcs in _iter_arcs_by_truck(arcs):
        color = colors[truck_id % len(colors)]
        edge_x, edge_y = [], []
        for arc in truck_arcs:
            edge_x.extend([arc["cust_from"]["xcoord"], arc["cust_to"]["xcoord"], None])
            edge_y.extend([arc["cust_from"]["ycoord"], arc["cust_to"]["ycoord"], None])

        traces.append(
            go.Scatter(
                x=edge_x,
                y=edge_y,
                mode="lines",
                line={"width": 1, "color": color},
                name=f"Truck {truck_id}",
                hoverinfo="skip",
            )
        )

        stops = _stops_for_truck(truck_arcs)
        if stops:
            traces.append(
                go.Scatter(
                    x=[c["xcoord"] for c in stops],
                    y=[c["ycoord"] for c in stops],
                    mode="markers",
                    marker={"size": 8, "color": color},
                    customdata=[c["cust_no"] for c in stops],
                    showlegend=False,
                    hovertemplate="Customer %{customdata}<br>X=%{x}<br>Y=%{y}<extra></extra>",
                )
            )

    # 2) Depot
    customers = _collect_customers(arcs)
    depot = [c for c in customers.values() if _is_depot(c)]

    if depot:
        traces.append(
            go.Scatter(
                x=[c["xcoord"] for c in depot],
                y=[c["ycoord"] for c in depot],
                mode="markers+text",
                marker={"size": 14, "symbol": "square", "color": "black"},
                text=["Depot"] * len(depot),
                textposition="top center",
                name="Depot",
                hovertemplate="Depot<br>X=%{x}<br>Y=%{y}<extra></extra>",
            )
        )

    return traces


def build_solution_chart(solution: SolutionResponse | None) -> go.Figure:
    traces = _build_chart_traces(solution) if solution is not None else []

    fig = go.Figure(traces)

    fig.update_layout(
        plot_bgcolor="white",
        xaxis_title="X",
        yaxis_title="Y",
        yaxis={"scaleanchor": "x", "scaleratio": 1},
    )

    return fig
