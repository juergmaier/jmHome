import os
# Run this app with `python thtUnterstand.py` and
# visit http://127.0.0.1:8050/ in your web browser.

#from flask import Flask

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from datetime import datetime as dt, timedelta
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from app import app
from datetime import datetime

meaco = dash.Dash(__name__)

colors = {'background': '#111111',
          'text': '#7FDBFF',
          'slider': 'yellow'}


# update graph periodically (defined by dcc.Interval(...))
@meaco.callback(Output('graphMeaco', 'figure'),
              Input('refreshInterval', 'n_intervals'),
              Input('lastXdays', 'value'))
def update_graph_live(n, numberOfDays):

    now = datetime.now()
    localFile = f"/home/juerg/homeAutomation/data/{kw-2}.csv"
    th1 = pd.read_csv(localFile, names=['Zeit', 'Ort', 'Typ', 'Wert'], header=None)
    th = th1.sort_values('Zeit')

    # show only last x days
    startTime = dt.today() - timedelta(days=10-numberOfDays)
    startTimeStr = startTime.strftime("%Y-%m-%d %H:%M:%S")
    thRecent = th[th.Zeit > startTimeStr]

    localFile = "/home/juerg/homeAutomation/collectData/taupunkt.csv"
    tp1 = pd.read_csv(localFile, names=['Zeit', 'Ort', 'Typ', 'Wert'], header=None)
    tp = tp1.sort_values('Zeit')

    # show only last x days
    tempAussenRecent = th[(th.Zeit > startTimeStr) & (th.Ort == 'aussen') & (th.Typ == 'temp')]
    tempUnterstandRecent = th[(th.Zeit > startTimeStr) & (th.Ort == 'unterstand') & (th.Typ == 'temp')]

    humidityAussenRecent = th[(th.Zeit > startTimeStr) & (th.Ort == 'aussen') & (th.Typ == 'humidity')]
    humidityUnterstandRecent = th[(th.Zeit > startTimeStr) & (th.Ort == 'unterstand') & (th.Typ == 'humidity')]

    taupunktAussenRecent = tp[(tp.Zeit > startTimeStr) & (tp.Ort == 'aussen') & (tp.Typ == 'taupunkt')]
    taupunktUnterstandRecent = tp[(tp.Zeit > startTimeStr) & (tp.Ort == 'unterstand') & (tp.Typ == 'taupunkt')]

    # show multiple scatter charts
    fig = make_subplots(rows=3, cols=1,
                        subplot_titles=('Temperatur','Feuchtigkeit','Taupunkt'),
                        shared_xaxes=True)
    fig.add_trace({'x': tempAussenRecent.Zeit,
                      'y': tempAussenRecent.Wert,
                      'type': 'scatter',
                      'name': 'aussen',
                      'line': go.scatter.Line(color='lightblue')}
                     ,1,1)
    fig.append_trace({'x': tempUnterstandRecent.Zeit,
                      'y': tempUnterstandRecent.Wert,
                      'type': 'scatter',
                      'name': 'unterstand',
                      'line': go.scatter.Line(color='red')}
                     ,1,1)

    fig.append_trace({'x': humidityAussenRecent.Zeit,
                      'y': humidityAussenRecent.Wert,
                      'type': 'scatter',
                      'name' : '',
                      'line': go.scatter.Line(color='lightblue')},
                     2,1)

    fig.append_trace({'x': humidityUnterstandRecent.Zeit,
                      'y': humidityUnterstandRecent.Wert,
                      'type': 'scatter',
                      'line': go.scatter.Line(color='red')},
                     2,1)

    fig.append_trace({'x': taupunktAussenRecent.Zeit,
                      'y': taupunktAussenRecent.Wert,
                      'type': 'scatter',
                      'line': go.scatter.Line(color='lightblue')},
                     3, 1)

    fig.append_trace({'x': taupunktUnterstandRecent.Zeit,
                      'y': taupunktUnterstandRecent.Wert,
                      'type': 'scatter',
                      'line': go.scatter.Line(color='red')}, 3, 1)

    fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        showlegend=False
    )
    return fig


def setLayout():
    currentTime = dt.now().strftime("%Y-%m-%d %H:%M")

    page = html.Div(
        style={'backgroundColor': colors['background']},
        children=[
            html.H1(children='Meaco',
                style={'textAlign': 'center',
                       'color': colors['text']}
            ),
            html.Div(
                html.Img(src=app.get_asset_url('meaco-ddl8.png')),
                style={'textAlign': 'center'}
            ),
            html.Div(children='Wahl der Anzahl Tage in der Vergangenheit:',
                     style={'margin-top': 10,
                            'textAlign': 'center',
                            'color': colors['slider']}
            ),
            html.Div(dcc.Slider(id='lastXdays', min=1, max=10, step=1, value=10-3,
                       marks={i:f'{i-10}' for i in range(10)}),
                        style={'margin-left': 50, 'margin-right': 50}),

            dcc.Graph(id='graphMeaco', style={'width':'150vh', 'height': '80vh'}),   #this id is referenced in the update_graph_live section

            dcc.Interval(id='refreshInterval', interval=1*60*1000, n_intervals=0),

            html.Meta(httpEquiv="refresh", content="900"),
        ])
    return page

layout = setLayout()      # caution, only reference the function, do not call it yet with setLayout()

