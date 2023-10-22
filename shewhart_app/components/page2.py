import random

from dash import dcc, html, dash_table, callback
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State

from shewhart_app.components.service.detectors import detect_trends, detect_shifts, detect_asterisks
from shewhart_app.components.service.models import Measurement, Base
from shewhart_app.components.service.session import Session, engine
import shewhart_app.components.content as content

MAX_POINTS = content.MAX_POINTS
mean_process_value = 100  # Среднее значение процесса
standard_deviation = 1  # Стандартное отклонение
sample_size = 5  # Размер выборки для каждой точки данных

# Для расчета контрольных пределов
UCL = mean_process_value + (3 * standard_deviation / (sample_size ** 0.5))
CL = mean_process_value
LCL = mean_process_value - (3 * standard_deviation / (sample_size ** 0.5))



# Список для хранения сгенерированных данных
values = []

ranges = []

# Контрольные пределы для R-чарта
R_bar = standard_deviation * 2.326  # Средний диапазон (приближенно для нормального распределения)
UCL_R = R_bar + 3 * (standard_deviation / (sample_size ** 0.5))
LCL_R = max(0, R_bar - 3 * (standard_deviation / (sample_size ** 0.5)))


layout = dbc.Container([
    html.H1("View p-Chart", className="mb-4"),
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
    Output('x-chart', 'figure'),
    [Input('interval-component-x-s-charts', 'n_intervals')]
)
def update_x_chart(n):
    # Добавляем новую точку данных на каждом обновлении
    new_value = mean_process_value + random.gauss(0, standard_deviation)
    values.append(new_value)

    # Создаем новый график
    trace = go.Scatter(
        y=values,
        mode='lines+markers',
        name='X-chart'
    )

    layout = go.Layout(
        title='X-chart: Control Chart for Mean',
        xaxis=dict(title='Sample'),
        yaxis=dict(title='Value'),
        showlegend=True,
        shapes=[
            # Линия среднего значения (CL)
            {
                'type': 'line',
                'x0': 0,
                'x1': len(values) - 1,
                'y0': CL,
                'y1': CL,
                'line': {
                    'color': 'blue',
                    'width': 2,
                    'dash': 'dashdot',
                }
            },
            # Верхний контрольный предел (UCL)
            {
                'type': 'line',
                'x0': 0,
                'x1': len(values) - 1,
                'y0': UCL,
                'y1': UCL,
                'line': {
                    'color': 'red',
                    'width': 2,
                    'dash': 'dash',
                }
            },
            # Нижний контрольный предел (LCL)
            {
                'type': 'line',
                'x0': 0,
                'x1': len(values) - 1,
                'y0': LCL,
                'y1': LCL,
                'line': {
                    'color': 'red',
                    'width': 2,
                    'dash': 'dash',
                }
            }
        ]
    )

    return {'data': [trace], 'layout': layout}


@callback(
    Output('r-chart', 'figure'),
    [Input('interval-component-x-s-charts', 'n_intervals')]
)
def update_r_chart(n):
    # Добавляем новый диапазон данных на каждом обновлении (мы предполагаем, что 'values' обновляется в X-chart)
    if len(values) >= sample_size:
        sample_group = values[-sample_size:]  # Получаем последние 'sample_size' точек данных
        range_value = max(sample_group) - min(sample_group)  # Вычисляем диапазон
        ranges.append(range_value)

    # Создаем новый график
    trace = go.Scatter(
        y=ranges,
        mode='lines+markers',
        name='R-chart'
    )

    layout = go.Layout(
        title='R-chart: Control Chart for Range',
        xaxis=dict(title='Sample Group'),
        yaxis=dict(title='Range'),
        showlegend=True,
        shapes=[
            # Линия среднего диапазона (R-bar)
            {
                'type': 'line',
                'x0': 0,
                'x1': len(ranges) - 1,
                'y0': R_bar,
                'y1': R_bar,
                'line': {
                    'color': 'blue',
                    'width': 2,
                    'dash': 'dashdot',
                }
            },
            # Верхний контрольный предел (UCL)
            {
                'type': 'line',
                'x0': 0,
                'x1': len(ranges) - 1,
                'y0': UCL_R,
                'y1': UCL_R,
                'line': {
                    'color': 'red',
                    'width': 2,
                    'dash': 'dash',
                }
            },
            # Нижний контрольный предел (LCL)
            {
                'type': 'line',
                'x0': 0,
                'x1': len(ranges) - 1,
                'y0': LCL_R,
                'y1': LCL_R,
                'line': {
                    'color': 'red',
                    'width': 2,
                    'dash': 'dash',
                }
            }
        ]
    )

    return {'data': [trace], 'layout': layout}