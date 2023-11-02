import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from shewhart_app.components.navbar import Navbar

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True, use_pages=True)
app.layout = html.Div([
    Navbar(),
    dash.page_container
])


# def redirect(pathname):
#     return dcc.Location(pathname=pathname, id='url-redirect', refresh=True)
#
#
# @app.callback(Output('page-content', 'children'),
#               [Input('url', 'pathname')])
# def display_page(pathname):
#     session = Session()
#     if re.match(r'^/bindings/\d+/input$', pathname):
#         binding_id = int(re.findall(r'\d+', pathname)[0])
#         binding = session.query(Binding).get(binding_id)
#         if binding:
#             return page1.layout_for_binding(binding_id)
#         else:
#             return redirect('/manage_bindings')
#     elif re.match(r'^/bindings/\d+/view$', pathname):
#         binding_id = int(re.findall(r'\d+', pathname)[0])
#         binding = session.query(Binding).get(binding_id)
#         if binding:
#             return page2.layout_for_binding(binding_id)
#         else:
#             return redirect('/manage_bindings')
#     elif pathname == '/manage_bindings':
#         return manage_bindings.layout()
#     else:
#         return redirect('/manage_bindings')


if __name__ == "__main__":
    app.run(debug=True)