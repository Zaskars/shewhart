import random

from dash import dcc, html, dash_table, callback
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State

from shewhart_app.components.service.detectors import detect_trends, detect_shifts, detect_asterisks, detect_asterisks_x, detect_shifts_x, detect_trends_x
from shewhart_app.components.service.models import Measurement, Base, XData, RData
from shewhart_app.components.service.session import Session, engine
import shewhart_app.components.content as content
from shewhart_app.components.service.constants import *

MAX_POINTS = content.MAX_POINTS
SAMPLE_SIZE = 5
MEAN = 10
STD_DEV = 2

layout = dbc.Container([
    html.H1("View p-Chart", className="mb-4"),
    html.Div(id='placeholder-x', style={'display': 'none'}),
    dcc.Graph(id="p-chart-page2"),
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
    )
])


@callback(
    Output("p-chart-page2", "figure"),
    [Input('interval-component-page2', 'n_intervals')],
)
def update_chart_page2(n_intervals):
    session = Session()
    recent_measurements = session.query(Measurement).order_by(Measurement.id.desc()).limit(MAX_POINTS)
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
    Input('interval-component-x-s-charts', 'n_intervals'),
)
def generate_x_data(n):
    session = Session()

    # Генерация новых данных
    new_values = np.random.normal(MEAN, STD_DEV, SAMPLE_SIZE)
    new_x = np.mean(new_values)
    new_r = np.max(new_values) - np.min(new_values)

    # Сохранение новых данных в базе данных
    new_x_data = XData(value=new_x, sample_size=SAMPLE_SIZE)
    new_r_data = RData(value=new_r, sample_size=SAMPLE_SIZE)
    session.add(new_x_data)
    session.add(new_r_data)
    session.commit()
    session.close()

    return ''


@callback(
    Output('x-chart', 'figure'),
    Input('interval-component-x-s-charts', 'n_intervals'),
)
def update_x_chart(n):
    session = Session()

    # Получение данных из базы данных
    x_data = session.query(XData).order_by(XData.id.desc()).limit(MAX_POINTS)
    x_data = x_data[::-1]

    # Подготовка данных для X-чарта
    x_values = [data.value for data in x_data]
    x_mean = np.mean(x_values)
    sample_size = x_data[0].sample_size if x_data else 5  # используйте реальный размер выборки

    x_ucl = x_mean + A2_values[sample_size] * np.std(x_values, ddof=1)
    x_lcl = x_mean - A2_values[sample_size] * np.std(x_values, ddof=1)

    is_trend, trend_text = detect_trends_x(x_values)
    is_shift, shift_text = detect_shifts_x(x_values, x_mean)
    is_asterisk, asterisk_text = detect_asterisks_x(x_values, x_mean)

    # Создание X-чарта
    x_chart = go.Figure()
    x_chart.add_trace(go.Scatter(y=x_values, mode='lines+markers', name='X'))

    # Если обнаружены аномалии, добавляем аннотации
    annotations = []
    if is_trend:
        annotations.append(
            {"x": len(x_values) - 1, "y": x_values[-1], "text": trend_text, "showarrow": True, "arrowhead": 7})
    if is_shift:
        annotations.append(
            {"x": len(x_values) - 1, "y": x_values[-1], "text": shift_text, "showarrow": True, "arrowhead": 7})
    if is_asterisk:
        annotations.append(
            {"x": len(x_values) - 1, "y": x_values[-1], "text": asterisk_text, "showarrow": True, "arrowhead": 7})

    x_chart.update_layout(annotations=annotations)

    x_chart.add_hline(y=x_mean, line_dash="dash", line_color="blue", annotation_text="Центральная линия",
                      annotation_position="bottom right")
    x_chart.add_hline(y=x_ucl, line_dash="dash", line_color="red", annotation_text="UCL",
                      annotation_position="bottom right")
    x_chart.add_hline(y=x_lcl, line_dash="dash", line_color="green", annotation_text="LCL",
                      annotation_position="top right")

    session.close()
    return x_chart


@callback(
    Output('r-chart', 'figure'),
    Input('interval-component-x-s-charts', 'n_intervals'),
)
def update_r_chart(n):
    session = Session()

    # Получение данных из базы данных
    r_data = session.query(RData).order_by(RData.id.desc()).limit(MAX_POINTS)
    r_data = r_data[::-1]

    # Подготовка данных для R-чарта
    r_values = [data.value for data in r_data]
    r_mean = np.mean(r_values)
    sample_size = r_data[0].sample_size if r_data else 5  # используйте реальный размер выборки

    r_ucl = D4_values[sample_size] * r_mean
    r_lcl = D3_values[sample_size] * r_mean

    is_trend, trend_text = detect_trends_x(r_values)
    is_shift, shift_text = detect_shifts_x(r_values, r_mean)
    is_asterisk, asterisk_text = detect_asterisks_x(r_values, r_mean)

    # Создание R-чарта
    r_chart = go.Figure()
    r_chart.add_trace(go.Scatter(y=r_values, mode='lines+markers', name='R'))

    # Если обнаружены аномалии, добавляем аннотации
    annotations = []
    if is_trend:
        annotations.append(
            {"x": len(r_values) - 1, "y": r_values[-1], "text": trend_text, "showarrow": True, "arrowhead": 7})
    if is_shift:
        annotations.append(
            {"x": len(r_values) - 1, "y": r_values[-1], "text": shift_text, "showarrow": True, "arrowhead": 7})
    if is_asterisk:
        annotations.append(
            {"x": len(r_values) - 1, "y": r_values[-1], "text": asterisk_text, "showarrow": True, "arrowhead": 7})

    r_chart.update_layout(annotations=annotations)

    r_chart.add_hline(y=r_mean, line_dash="dash", line_color="blue", annotation_text="Центральная линия",
                      annotation_position="bottom right")
    r_chart.add_hline(y=r_ucl, line_dash="dash", line_color="red", annotation_text="UCL",
                      annotation_position="bottom right")
    r_chart.add_hline(y=r_lcl, line_dash="dash", line_color="green", annotation_text="LCL",
                      annotation_position="top right")

    session.close()
    return r_chart
