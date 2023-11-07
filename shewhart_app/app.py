import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from shewhart_app.components.navbar import Navbar

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True, use_pages=True)
app.layout = html.Div([
    Navbar(),
    dash.page_container
])

if __name__ == "__main__":
    app.run(debug=True)
