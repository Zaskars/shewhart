import random
import re
import dash
from dash import dcc, html, dash_table, callback
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State

from shewhart_app.components.service.detectors import detect_trends, detect_shifts, detect_asterisks, \
    detect_asterisks_x, detect_shifts_x, detect_trends_x
from shewhart_app.components.service.models import Measurement, Base, XData, RData, IndividualMeasurement
from shewhart_app.components.service.session import Session, engine
import shewhart_app.components.content as content
from shewhart_app.components.service.constants import *
from shewhart_app.components.navbar import Navbar

MAX_POINTS = content.MAX_POINTS
SAMPLE_SIZE = 5
MEAN = 10
STD_DEV = 2

dash.register_page(__name__, path_template='/bindings/<bid>/view')


def layout(bid=None):
    return dbc.Container([
        html.H1(f"View {bid}", className="mb-4"),
        html.Div(id='placeholder-x', style={'display': 'none'}),
        dcc.Graph(id="p-chart-page2"),
        dbc.Row([
            dbc.Col([
                dbc.Label("Subgroup Size"),
                dcc.Input(
                    id="input-subgroup-size",
                    type="number",
                    placeholder="Enter subgroup size",
                    value=5,  # Значение по умолчанию
                ),
                dbc.Button(
                    "Update Chart",
                    id="update-chart-button",
                    color="primary",
                    className="mt-2"
                ),
            ], width=4),
        ]),
        dcc.Graph(id="x-chart"),
        dcc.Graph(id="r-chart"),
        dcc.Interval(
            id='interval-component-page2',
            interval=10 * 1000,  # in milliseconds
            n_intervals=0
        ),
        dcc.Interval(
            id='interval-component-x-s-charts',
            interval=5 * 1000,  # обновление каждые 5 секунд
            n_intervals=0
        ),
        html.Data(id='bid', value=bid)
    ])


@callback(
    Output("p-chart-page2", "figure"),
    [Input('interval-component-page2', 'n_intervals')],
    State("bid", "value")
)
def update_chart_page2(n_intervals, bid):
    binding_id = int(bid)
    session = Session()
    recent_measurements = session.query(Measurement).filter_by(binding_id=binding_id).order_by(
        Measurement.id.desc()).limit(MAX_POINTS)
    recent_measurements = recent_measurements[::-1]  # если требуется обратный порядок
    session.close()

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

    return figure


@callback(
    Output('placeholder-x', 'children'),
    [Input('interval-component-x-s-charts', 'n_intervals')],
    State("bid", "value")
)
def generate_x_data(n, bid):
    binding_id = int(bid)
    session = Session()

    # Генерация новых данных
    new_values = np.random.normal(MEAN, STD_DEV, SAMPLE_SIZE)
    new_x = np.mean(new_values)
    new_r = np.max(new_values) - np.min(new_values)

    # Сохранение новых данных в базе данных
    new_x_data = XData(value=new_x, sample_size=SAMPLE_SIZE, binding_id=binding_id)
    new_r_data = RData(value=new_r, sample_size=SAMPLE_SIZE, binding_id=binding_id)
    session.add(new_x_data)
    session.add(new_r_data)
    session.commit()
    session.close()

    return ''


@callback(
    Output('x-chart', 'figure'),
    [Input('interval-component-x-s-charts', 'n_intervals'),
     Input('update-chart-button', 'n_clicks')],
    [State("bid", "value"), State("input-subgroup-size", "value")]
)
def update_x_chart(n_intervals, n_clicks, bid, sample_size):
    binding_id = int(bid)
    session = Session()

    # Получение данных из базы данных
    individual_measurements = session.query(IndividualMeasurement).filter_by(binding_id=binding_id).order_by(
        IndividualMeasurement.id.desc()).limit(MAX_POINTS*sample_size).all()
    individual_measurements_list = np.array([data.value for data in individual_measurements])
    individual_measurements_list = individual_measurements_list[::-1]


    session.close()

    # Группировка данных в подгруппы
    grouped_measurements = [individual_measurements_list[i:i + sample_size] for i in
                            range(0, len(individual_measurements_list), sample_size) if
                            len(individual_measurements_list[i:i + sample_size]) == sample_size]



    # Расчет средних значений и стандартных отклонений для каждой подгруппы
    subgroup_means = np.array([np.mean(subgroup) for subgroup in grouped_measurements])
    subgroup_stddevs = np.array([np.std(subgroup, ddof=1) for subgroup in grouped_measurements])
    x_mean = np.mean(subgroup_means)
    print(subgroup_means)

    # Расчет контрольных пределов для каждой подгруппы
    a2 = A2_values.get(sample_size, A2_values[
        5])  # Получаем значение A2 для размера подгруппы, по умолчанию используем для размера 5
    x_ucl = np.ones((len(subgroup_means),), dtype=int) * x_mean + a2 * np.mean(subgroup_stddevs)
    x_lcl = np.ones((len(subgroup_means),), dtype=int) * x_mean - a2 * np.mean(subgroup_stddevs)
    # Создание X-чарта
    annotations = []
    is_trend, trend_text = detect_trends_x(subgroup_means)

    is_shift, shift_text = detect_shifts_x(subgroup_means, x_mean)
    is_asterisk, asterisk_text = detect_asterisks_x(subgroup_means, x_mean)

    # Создание R-чарта
    if is_trend:
        annotations.append(
            dict(
                x=len(subgroup_means) - 1,
                y=subgroup_means[-1],
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
                x=len(subgroup_means) - 1,
                y=subgroup_means[-1],
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
                x=len(subgroup_means) - 1,
                y=subgroup_means[-1],
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
            go.Scatter(y=subgroup_means, mode="lines+markers", name="Value", line=dict(color='blue')),
            go.Scatter(y=[x_mean for _ in subgroup_means], name="Mean Value"),
            go.Scatter(y=x_ucl, mode="lines", name="UCL", line=dict(dash="dash", color='red')),
            go.Scatter(y=x_lcl, mode="lines", name="LCL", line=dict(dash="dash", color='red'))

        ],
        'layout': go.Layout(
            title="X-Chart",
            xaxis=dict(title="Sample Number"),
            yaxis=dict(title="Value"),
            showlegend=True,
            annotations=annotations
        )
    }

    return figure


@callback(
    Output('r-chart', 'figure'),
    [Input('interval-component-x-s-charts', 'n_intervals')],
    State("bid", "value")
)
def update_r_chart(n, bid):
    binding_id = int(bid)
    session = Session()

    # Получение данных из базы данных
    r_data = session.query(RData).filter_by(binding_id=binding_id).order_by(RData.id.desc()).limit(MAX_POINTS)
    session.close()
    r_data = r_data[::-1]

    # Подготовка данных для R-чарта
    r_values = np.array([data.value for data in r_data])
    r_mean = np.mean(r_values)
    sample_size = r_data[0].sample_size if r_data else 5

    r_ucl = np.ones((len(r_values),), dtype=int) * D4_values[sample_size] * r_mean
    r_lcl = np.ones((len(r_values),), dtype=int) * D3_values[sample_size] * r_mean

    annotations = []
    is_trend, trend_text = detect_trends_x(r_values)
    is_shift, shift_text = detect_shifts_x(r_values, r_mean)
    is_asterisk, asterisk_text = detect_asterisks_x(r_values, r_mean)

    # Создание R-чарта
    if is_trend:
        annotations.append(
            dict(
                x=len(r_values) - 1,
                y=r_values[-1],
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
                x=len(r_values) - 1,
                y=r_values[-1],
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
                x=len(r_values) - 1,
                y=r_values[-1],
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
            go.Scatter(y=r_values, mode="lines+markers", name="Standard Deviation", line=dict(color='blue')),
            go.Scatter(y=[r_mean for _ in r_values], name="Mean Value"),
            go.Scatter(y=r_ucl, mode="lines", name="UCL", line=dict(dash="dash", color='red')),
            go.Scatter(y=r_lcl, mode="lines", name="LCL", line=dict(dash="dash", color='red'))

        ],
        'layout': go.Layout(
            title="R-Chart",
            xaxis=dict(title="Sample Number"),
            yaxis=dict(title="Standart Deviation"),
            showlegend=True,
            annotations=annotations
        )
    }

    return figure
