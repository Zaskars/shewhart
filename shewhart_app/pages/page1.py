import json
import re
import dash
from dash import dcc, html, dash_table, callback
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State, MATCH, ALL

from shewhart_app.components.service.detectors import detect_trends, detect_shifts, detect_asterisks
from shewhart_app.components.service.models import Measurement, Base, IndividualMeasurement, Chart, Binding
from shewhart_app.components.service.session import Session, engine
import shewhart_app.components.content as content
from shewhart_app.components.navbar import Navbar

Base.metadata.create_all(engine)
MAX_POINTS = content.MAX_POINTS

dash.register_page(__name__, path_template='/bindings/<bid>/input')


def layout(bid=None):
    session = Session()
    binding_id = int(bid)
    binding = session.query(Binding).filter_by(id=binding_id).one_or_none()

    charts_data_input_forms = []
    if binding and binding.charts:
        for chart in binding.charts:
            chart_form = dbc.Row([
                dbc.Col([
                    html.H4(chart.name),
                    dbc.Label("Enter Data for " + chart.name),
                    dbc.Input(id={"type": "input-data", "index": chart.id}, type="number", step="any",
                              className="mb-2"),
                    dbc.Button("Add Data to " + chart.name, id={"type": "add-data-button", "index": chart.id},
                               color="primary", className="mb-3"),
                ], width=4),
            ])
            charts_data_input_forms.append(chart_form)
    session.close()
    return dbc.Container([
        html.H1(f"Input for Binding {bid}", className="mb-4"),  # заголовок гребаный
        dbc.Row([
            dbc.Col([
                dbc.Label("Proportion (e.g., 0.11)"),
                dbc.Input(id=f"input-proportion", type="number", step=0.001, className="mb-2"),
                dbc.Label("Sample Size (e.g., 100)"),
                dbc.Input(id=f"input-sample-size", type="number", className="mb-2"),
                dbc.Button("Add Data", id=f"add-data-button", color="primary", className="mb-3"),
            ], width=4),
            dbc.Col([
                dash_table.DataTable(
                    id=f'table',
                    columns=[
                        {"name": "Proportion", "id": "proportion"},
                        {"name": "Sample Size", "id": "sample_size"},
                    ],
                    style_table={'height': '300px', 'overflowY': 'auto'},
                    data=[],
                ),
            ], width=4),
        ]),

        dcc.Graph(id=f"p-chart"),
        html.Div(id=f'data-added-signal', style={'display': 'none'}),
        dcc.Interval(
            id=f'interval-component',
            interval=10 * 1000,  # in milliseconds
            n_intervals=0
        ),
        dbc.Row([
            dbc.Col([
                dbc.Label("New Chart Name"),
                dbc.Input(id="input-new-chart-name", type="text", className="mb-2"),
                dbc.Button("Create New Chart", id="create-new-chart-button", color="success", className="mb-3"),
            ], width=4),
        ]),
        html.Div(charts_data_input_forms, id="charts-data-input-container"),
        html.Div(id='data-added-signal-x', style={'display': 'none'}),
        html.Div(id='data-added-signal-2', style={'display': 'none'}),
        html.Div(id='create-chart-signal', style={'display': 'none'}),
        html.Data(id='bid', value=bid)
    ])


@callback(
    Output('create-chart-signal', 'children'),
    [Input("create-new-chart-button", "n_clicks")],
    [State("input-new-chart-name", "value"),
     State("bid", "value")]
)
def create_new_chart(n_clicks, chart_name, bid):
    print('here')
    if n_clicks and chart_name:
        binding_id = int(bid)
        session = Session()
        new_chart = Chart(name=chart_name, binding_id=binding_id)
        session.add(new_chart)
        session.commit()
        session.close()
        return 'Chart Created'
    return ''


@callback(
    Output('data-added-signal', 'children'),
    [Input("add-data-button", "n_clicks")],
    [State("input-proportion", "value"),
     State("input-sample-size", "value"),
     State("bid", "value")]
)
def add_data_to_database(n_clicks, proportion, sample_size, bid):
    binding_id = int(bid)

    if n_clicks and proportion is not None and sample_size is not None:
        session = Session()
        new_measurement = Measurement(proportion=proportion, sample_size=sample_size, binding_id=binding_id)
        session.add(new_measurement)
        session.commit()
        session.close()
        return 'True'  # данные успешно добавлены
    return 'False'


@callback(
    Output('data-added-signal-2', 'children'),
    [Input({"type": "add-data-button", "index": ALL}, "n_clicks")],
    [State({"type": "input-data", "index": ALL}, "value"),  # Добавленный state для идентификатора чарта
     State("bid", "value")]
)
def add_individual_data_to_database(all_clicks, all_input_values, bid):
    ctx = dash.callback_context
    if not ctx.triggered:
        return 'No clicks yet'

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    chart_id = json.loads(button_id)["index"]

    # Проверяем, какая кнопка была нажата
    button_clicked_index = [i for i, n in enumerate(all_clicks) if n is not None]
    if button_clicked_index:
        clicked_index = button_clicked_index[0]
        input_value = all_input_values[clicked_index]
        if input_value is not None:
            binding_id = int(bid)
            chart_id = int(chart_id)  # Преобразуем chart_id в int

            session = Session()
            new_measurement = IndividualMeasurement(
                value=input_value,
                binding_id=binding_id,
                chart_id=chart_id
            )
            session.add(new_measurement)
            session.commit()
            session.close()
            return 'True'  # данные успешно добавлены
    return 'False'



@callback(
    [Output("table", "data"),
     Output("p-chart", "figure")],
    [Input('data-added-signal', 'children'),
     Input('interval-component', 'n_intervals')],
    State("bid", "value")
)
def update_chart(data_added, n_intervals, bid):
    binding_id = int(bid)
    session = Session()
    recent_measurements = session.query(Measurement).filter_by(binding_id=binding_id).order_by(
        Measurement.id.desc()).limit(MAX_POINTS)
    recent_measurements = recent_measurements[::-1]
    session.close()

    # Обновление текстового поля и графика
    table_data = [{"proportion": m.proportion, "sample_size": m.sample_size} for m in recent_measurements]

    proportions = [m.proportion for m in recent_measurements]
    sample_sizes = [m.sample_size for m in recent_measurements]

    proportions = np.array(proportions)
    sample_sizes = np.array(sample_sizes)

    p_bar = np.sum(proportions * sample_sizes) / np.sum(sample_sizes)
    sigmas = np.sqrt(p_bar * (1 - p_bar) / sample_sizes)
    UCLs = p_bar + 3 * sigmas
    sig2 = p_bar + 2 * sigmas
    sig1 = p_bar + sigmas
    LCLs = np.maximum(0, p_bar - 3 * sigmas)
    lsig2 = np.maximum(0, p_bar - 2 * sigmas)
    lsig1 = np.maximum(0, p_bar - sigmas)

    annotations = []
    is_trend, trend_text = detect_trends(proportions)
    is_shift, shift_text = detect_shifts(proportions, p_bar)
    is_asterisk, asterisk_text = detect_asterisks(proportions, p_bar)

    if is_trend:
        annotations.append(
            dict(
                x=len(proportions) - 1,
                y=proportions[-1],
                xref="x",
                yref="y",
                text=trend_text,
                showarrow=True,
                arrowhead=7,
                ax=0,
                ay=-40
            )
        )
    if is_shift:
        annotations.append(
            dict(
                x=len(proportions) - 1,
                y=proportions[-1],
                xref="x",
                yref="y",
                text=shift_text,
                showarrow=True,
                arrowhead=7,
                ax=0,
                ay=-70
            )
        )
    if is_asterisk:
        annotations.append(
            dict(
                x=len(proportions) - 1,
                y=proportions[-1],
                xref="x",
                yref="y",
                text=asterisk_text,
                showarrow=True,
                arrowhead=7,
                ax=0,
                ay=-100
            )
        )

    figure = {
        'data': [
            go.Scatter(y=proportions, mode="lines+markers", name="Proportion", line=dict(color='blue')),
            go.Scatter(y=[p_bar for _ in proportions], mode="lines", name="Mean Proportion"),
            go.Scatter(y=UCLs, mode="lines", name="UCL (+3σ)", line=dict(dash="dash", color='red')),
            go.Scatter(y=sig2, mode="lines", name="2σ", line=dict(dash="dash", color='orange')),
            go.Scatter(y=sig1, mode="lines", name="σ", line=dict(dash="dash", color='purple')),
            go.Scatter(y=lsig1, mode="lines", name="-σ", line=dict(dash="dash", color='purple')),
            go.Scatter(y=lsig2, mode="lines", name="-2σ", line=dict(dash="dash", color='orange')),
            go.Scatter(y=LCLs, mode="lines", name="LCL (-3σ)", line=dict(dash="dash", color='red'))

        ],
        'layout': go.Layout(
            title="Custom p-Chart with Floating Control Limits",
            xaxis=dict(title="Sample Number"),
            yaxis=dict(title="Proportion"),
            showlegend=True,
            annotations=annotations
        )
    }

    return table_data, figure
