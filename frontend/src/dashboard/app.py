import dash_bootstrap_components as dbc
from dash import Dash

from dashboard.layout import build_layout
from dashboard.settings import DEBUG, HOST, PORT


def create_app() -> Dash:
    """
    Dash app factory. Returns a Dash app instance.
    """
    app = Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB])

    app.layout = build_layout()

    from dashboard import callbacks  # noqa: F401

    return app


def main() -> None:
    app = create_app()
    app.run(debug=DEBUG, host=HOST, port=PORT)


app = create_app()
