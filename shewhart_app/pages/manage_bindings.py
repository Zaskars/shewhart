from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from shewhart_app.components.service.models import Binding
from shewhart_app.components.service.session import Session
from shewhart_app.components.navbar import Navbar

dash.register_page(__name__, path="/")

layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                html.H1("Manage Bindings", className="mb-4"),
                className="text-center",  # Text centering
            )
        ),
        dbc.Input(
            id="binding-name",
            placeholder="Enter binding name...",
            type="text",
            className="mb-3",
        ),
        dbc.Button(
            "Add Binding", id="add-binding-button", color="primary", className="mb-3"
        ),
        html.Div(id="binding-list"),
    ]
)


@callback(
    Output("binding-list", "children"),
    [Input("add-binding-button", "n_clicks")],
    [State("binding-name", "value")],
)
def manage_bindings(n_clicks, binding_name):
    session = Session()

    # Если имя связки предоставлено, добавляем его в базу данных
    if n_clicks and binding_name:
        new_binding = Binding(name=binding_name)
        session.add(new_binding)
        session.commit()

    # Получаем список всех связок
    bindings = session.query(Binding).all()
    session.close()

    binding_elements = []
    for binding in bindings:
        card_content = dbc.CardBody(
            [
                html.H4(binding.name, className="card-title"),
                dbc.Button(
                    "Input",
                    href=f"/bindings/{binding.id}/input",
                    color="primary",
                    className="me-2",
                ),
                dbc.Button(
                    "View", href=f"/bindings/{binding.id}/view", color="secondary"
                ),
            ]
        )
        card = dbc.Card(card_content, className="mb-3")
        binding_elements.append(card)

    return html.Div(binding_elements)
