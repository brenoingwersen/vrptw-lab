import dash_ag_grid as dag
import dash_bootstrap_components as dbc


def runs_table() -> dbc.Row:
    """
    Build the runs table component.
    """
    column_defs = [
        {
            "headerName": "Run ID",
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
            "headerName": "Created At",
            "field": "created_at",
            "filter": "agTextColumnFilter",
            "filterParams": {
                "buttons": ["reset", "apply"],
            },
        },
        {
            "headerName": "Finished At",
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
    return dag.AgGrid(
        id="runs-table",
        rowData=[],
        columnDefs=column_defs,
        columnSize="sizeToFit",
        defaultColDef={"flex": 1, "filter": True},
        dashGridOptions={
            "animateRows": False,
            "rowSelection": {"mode": "singleRow", "enableClickSelection": True},
        },
        selectedRows=[],
    )
