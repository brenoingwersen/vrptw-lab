import dash_bootstrap_components as dbc
from dash import Dash

from dashboard.layout import build_layout


def create_app() -> Dash:
    """
    Dash app factory. Returns a Dash app instance.
    """

    app = Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB])

    app.layout = build_layout()

    from dashboard import callbacks  # noqa: F401

    app.run(debug=True)
    return app
