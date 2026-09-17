from dash import Dash
import dash_bootstrap_components as dbc

from dashboard.layout import build_layout


def create_app() -> Dash:
    """
    Dash app factory function.
    """

    app = Dash(
        __name__, external_stylesheets=[dbc.themes.SPACELAB], assets_folder="assets"
    )

    app.layout = build_layout()

    from dashboard.callbacks import callback

    app.run(debug=True)
    return app
