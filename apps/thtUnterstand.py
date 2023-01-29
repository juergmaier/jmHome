# Run this app with `python index.py` then
# visit http://127.0.0.1:8050/ in your web browser.

#from flask import Flask

import os
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
from datetime import datetime as dt, timedelta
from plotly.subplots import make_subplots
import plotly.graph_objects as go

import config
from app import app


colors = {'background': '#111111',
          'text': '#7FDBFF',
          'slider': 'yellow'}


def loadData(typ, ort, zeit, numberOfDays):

    dfList = []
    # setze die startzeit für das einlesen der daten
    startZeit = zeit - timedelta(days=10-numberOfDays)

    # filename is {year}_{kw}.csv
    # load numberOfDays data backward from zeit
    lastKw = 99
    datenZeit = startZeit
    while datenZeit <= zeit:
        thisKw = datenZeit.isocalendar()[1]

        if thisKw != lastKw:
            lastKw = thisKw
            filePath = f"{config.absPfadDaten}/{typ}/{ort}/{datenZeit.year}_{thisKw:02.0f}.csv"
            if os.path.exists(filePath):
                data = pd.read_csv(filePath, names=['zeit', 'wert'], header=None)
                dfList.append(data)

        datenZeit = datenZeit + timedelta(days=1)
        #print(f"new datenZeit {datenZeit}")

    # fasse die KW-Daten in ein dataframe zusammen
    if len(dfList) == 0:
        return None

    # fasse die KW-Daten in ein dataframe zusammen
    dfAll = pd.concat(dfList)

    # limitiere die Daten auf numberOfDays
    dfLimited = dfAll[dfAll['zeit'] >= str(startZeit)]

    # und sortiere nach Zeit
    return dfLimited.sort_values(['zeit'])


# update graph periodically (defined by dcc.Interval(...))
@app.callback(Output('graphUnterstand', 'figure'),
              Input('refreshInterval', 'n_intervals'),
              Input('lastXdays', 'value'))
def update_graph_live(n, numberOfDays):
    print(f"update_graph_live Unterstand {n=}, {numberOfDays=}")

    taData = loadData('temperatur', 'unterstandAussen', dt.now(), numberOfDays)
    tiData = loadData('temperatur', 'unterstandInnen', dt.now(), numberOfDays)
    faData = loadData('feuchtigkeit', 'unterstandAussen', dt.now(), numberOfDays)
    fiData = loadData('feuchtigkeit', 'unterstandInnen', dt.now(), numberOfDays)
    paData = loadData('taupunkt', 'unterstandAussen', dt.now(), numberOfDays)
    piData = loadData('taupunkt', 'unterstandInnen', dt.now(), numberOfDays)
    fanData = loadData('ein-aus', 'entfeuchterUnterstand', dt.now(), numberOfDays)

    # show multiple scatter charts
    fig = make_subplots(rows=5, cols=1,
                        subplot_titles=('Temperatur',
                                        'Feuchtigkeit',
                                        'Taupunkt',
                                        'Diff Temperatur innen - Taupunkt innen'),
                        shared_xaxes=True)

    fig.add_trace({'x': taData.zeit,
                   'y': taData.wert,
                   'type': 'scatter',
                   'name': 'Aussen',
                   'line': go.scatter.Line(color='greenyellow')},
                   1,1)

    fig.add_trace({'x': tiData.zeit,
                   'y': tiData.wert,
                   'type': 'scatter',
                   'name': 'Innen',
                   'line': go.scatter.Line(color='lime')},
                   1,1)

    fig.add_trace({'x': faData.zeit,
                   'y': faData.wert,
                   'type': 'scatter',
                   'name' : '',
                   'line': go.scatter.Line(color='greenyellow')},
                   2,1)

    fig.add_trace({'x': fiData.zeit,
                   'y': fiData.wert,
                   'type': 'scatter',
                   'name': '',
                   'line': go.scatter.Line(color='lime')},
                   2,1)

    fig.add_trace({'x': paData.zeit,
                   'y': paData.wert,
                   'type': 'scatter',
                   'name':'',
                   'line': go.scatter.Line(color='greenyellow')},
                   3, 1)

    fig.add_trace({'x': piData.zeit,
                   'y': piData.wert,
                   'type': 'scatter',
                   'name': '',
                   'line': go.scatter.Line(color='lime')},
                  3, 1)

    fig.add_trace({'x': piData.zeit,
                   'y': tiData.wert - piData.wert,
                   'type': 'scatter',
                   'name': '',
                   'line': go.scatter.Line(color='lime')},
                  4, 1)
    if fanData is not None:
        fig.add_trace({'x': fanData.zeit,
                       'y': fanData.wert,
                       'type': 'scatter',
                       'line_shape': "hv",
                       'name': 'Entfeuchter',
                       'line': go.scatter.Line(color='lime')},
                       5, 1)


    fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        showlegend=True
    )
    return fig


def setLayout():
    #print("tht setLayout")
    currentTime = dt.now().strftime("%Y-%m-%d %H:%M")
    page = html.Div(
        style={'backgroundColor': colors['background']},
        children=[
            html.Div(children='Wahl der Anzahl Tage in der Vergangenheit:',
                     style={'margin-top': 10,
                            'textAlign': 'center',
                            'color': colors['slider']}
            ),
            html.Div(dcc.Slider(id='lastXdays', min=1, max=10, step=1, value=5,
                       marks={i:f'{i-10}' for i in range(10)}),
                        style={'margin-left': 50, 'margin-right': 50}),

            # this id is referenced in the update_graph_live section
            dcc.Graph(id='graphUnterstand', style={'margin-left': 50, 'margin-right': 50, 'height': '80vh'}),

            dcc.Interval(id='refreshInterval', interval=1*60*1000, n_intervals=0),

            html.Meta(httpEquiv="refresh", content="900"),
        ])
    return page

layout = setLayout()      # ??? caution, only reference the function, do not call it yet with setLayout()

