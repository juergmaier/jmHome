
# this is part of JMHome index.py
# it shows the power consumption in kWh of the meross switches

import os
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
from datetime import datetime as dt, timedelta
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from app import app
import config

colors = {'background': '#111111',
          'text': '#7FDBFF',
          'slider': 'yellow'}


def loadData(typ, ort, zeit, numberOfWeeks):

    dfList = []
    startZeit = zeit - timedelta(days=(10-numberOfWeeks)*7)
    #print(f"{startZeit=}")

    # filename is {year}_{kw}.csv
    # load numberOfDays data backward from zeit
    lastKw = 99
    datenZeit = startZeit
    while datenZeit <= zeit:
        thisKw = datenZeit.isocalendar()[1]
        if thisKw != lastKw:
            lastKw = thisKw
            filePath = f"{config.absPfadDaten}/{typ}/{ort}/{datenZeit.year}_{thisKw:02.0f}.csv"
            if os.path.isfile(filePath):
                data = pd.read_csv(filePath, names=['zeit', 'wert'], header=None)
                #print(f"readFile: {filePath}")
                dfList.append(data)
        datenZeit = datenZeit + timedelta(days=1)
        #print(f"new datenZeit {datenZeit}")

    # fasse die KW-Daten in ein dataframe zusammen
    if len(dfList) == 0:
        return None

    dfAll = pd.concat(dfList)

    # limitiere die Daten auf numberOfDays
    dfLimited = dfAll[dfAll['zeit'] >= str(startZeit)]

    # und sortiere nach Zeit
    return dfLimited.sort_values(['zeit'])


# update graph periodically (defined by dcc.Interval(...))
@app.callback(Output('graphStrom', 'figure'),
              Input('refreshInterval', 'n_intervals'),
              Input('lastXdays', 'value'))
def update_graph_live(n, numberOfDays):

    data = []
    names = []

    print(f"update_graph_live {n=}, {numberOfDays=}")

    rootDir = config.absPfadDaten + "/stromverbrauch"
    for rootDir, dirs, files in os.walk(rootDir):
        for dir in dirs:
            print(f"load data: {dir}")
            dirData = loadData('stromverbrauch', dir, dt.now(), numberOfDays)
            if dirData is not None:
                data.append(dirData)
                names.append("kWh " + dir)
            else:
                pass

    # show multiple scatter charts
    fig = make_subplots(rows=len(names), cols=1,
                        subplot_titles=(names),
                        shared_xaxes=True)

    for i in range(len(names)):
        fig.add_trace({'x': data[i].zeit,
                       'y': data[i].wert,
                       'type': 'scatter',
                       'line': go.scatter.Line(color='cyan')},
                       i+1,1)

        fig.update_yaxes(row=i+1, col=1, range=[0,4])

    fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color='white',
        showlegend=False
    )

    return fig


def setStromLayout():
    #print("strom setLayout")
    currentTime = dt.now().strftime("%Y-%m-%d %H:%M")
    page = html.Div(
        style={'backgroundColor': colors['background']},
        children=[
            html.Div(children='Wahl der Anzahl Wochen in der Vergangenheit:',
                     style={'margin-top': 10,
                            'textAlign': 'center',
                            'color': colors['slider']}
            ),
            html.Div(dcc.Slider(id='lastXdays', min=1, max=10, step=1, value=5,
                       marks={i:f'{i-10}' for i in range(10)}),
                        style={'margin-left': 50, 'margin-right': 50}),

            # this id is referenced in the update_graph_live section
            dcc.Graph(id='graphStrom', style={'margin-left': 50, 'margin-right': 50, 'height': '80vh'}),

            dcc.Interval(id='refreshInterval', interval=1*60*1000, n_intervals=0),

            html.Meta(httpEquiv="refresh", content="900"),
        ])
    return page

layout = setStromLayout()      # ??? caution, only reference the function, do not call it yet with setLayout()

