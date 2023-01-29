


import os
from datetime import datetime
import config

from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
from datetime import datetime as dt, timedelta
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from app import app


colors = {'background': '#111111',
          'text': '#7FDBFF',
          'slider': 'yellow'}

linecolors = {'kWh': ("cyan", "cyan", "red"),
              'TempMean': "red",
              'TempMin': "blue",
              'TempMax': "blue"}


def loadData(typ, ort, zeit, numberOfWeeks):

    dfList = []
    startZeit = zeit - timedelta(days=(10-numberOfWeeks)*7)

    # filename is {year}_{kw}.csv
    # load numberOfWeeks data backward from zeit
    lastKw = 99
    datenZeit = startZeit
    while datenZeit <= zeit:
        thisKw = datenZeit.isocalendar()[1]
        if thisKw != lastKw:
            lastKw = thisKw
            filePath = f"{config.absPfadDaten}/{typ}/{ort}/{datenZeit.year}_{thisKw:02.0f}.csv"
            if os.path.isfile(filePath):
                data = pd.read_csv(filePath, names=['zeit', 'wert'], header=None)

                # beschränke zeit auf tag
                data['zeit'] = [item[0:10] for item in data['zeit']]

                # und ergänze eine diff spalte
                data['diffW'] = 0
                dfList.append(data)
        datenZeit = datenZeit + timedelta(days=1)

    # fasse die KW-Daten in ein dataframe zusammen
    if len(dfList) == 0:
        return None

    dfAll = pd.concat(dfList)

    # limitiere die Daten auf numberOfWeeks
    dfLimited = dfAll[dfAll['zeit'] >= str(startZeit)]

    # und sortiere nach Zeit
    #return dfLimited.sort_values(['zeit'])
    dfSorted = dfLimited.sort_values(['zeit'])

    # addiere eine differenz-column zu vorgängerwert
    differenz = dfSorted['wert'] - dfSorted['wert'].shift(1, fill_value=0)
    differenz.mask(differenz > 80, 0, inplace=True)
    dfSorted.loc[:,'diffW'] = differenz

    # keine negativen zahlen in diff
    dfSorted.loc[:,['diffW']][dfSorted['diffW'] < 0] = 0
    #dfSorted.loc[:, ['diffW']][dfSorted['diffW'] > 100] = 0

    return dfSorted

# die täglichen temperaturbereiche sind in einem weiteren csv abgelegt mit
# date, mean, min, max
def loadDailyTemp(numberOfWeeks):
    startZeit = datetime.now() - timedelta(days=(10 - numberOfWeeks) * 7)
    dfAll = pd.read_csv("../data/temperatur/dailyTotal.csv", names=['tag', 'mean', 'min', 'max'], header=None)
    dfTemp = dfAll[dfAll['tag'] >= str(startZeit)[:10]]      # limitiere start-datum
    return dfTemp

# die total betriebsstunden der wärmepumpe sind in einem eigenen csv abgelegt mit
# tag, betriebsstunden
def loadWpStunden(numberOfWeeks):
    startZeit = datetime.now() - timedelta(days=(10 - numberOfWeeks) * 7)
    dfAll = pd.read_csv("../data/wpBetriebsstunden/dailyValues.csv", names=['tag', 'stunden'], header=None)
    dfWpStunden = dfAll[dfAll['tag'] >= str(startZeit)[0:10]]      # limitiere start-datum
    dfSorted = dfWpStunden.sort_values(['tag'])
    # addiere eine differenz-column zu vorgängerwert
    differenz = dfSorted['stunden'] - dfSorted['stunden'].shift(1, fill_value=0)
    differenz.mask(differenz > 24, 0, inplace=True)
    dfSorted.loc[:,'diffH'] = differenz

    # keine negativen zahlen in diff
    dfSorted.loc[:, ['diffH']][dfSorted['diffH'] < 0] = 0

    return dfSorted


# update graph periodically (defined by dcc.Interval(...))
@app.callback(Output('graphZaehlerEW', 'figure'),
              Input('refreshInterval', 'n_intervals'),
              Input('lastXweeks', 'value'))
def update_graph_live(n, numberOfWeeks):

    data = []
    names = []

    #print(f"update_graph_live {n=}, {numberOfWeeks=}")

    rootDir = config.absPfadDaten + "/stromzaehler"
    for rootDir, dirs, files in os.walk(rootDir):
        for dir in dirs:        # zählertyp 181 und 182
            print(f"load data: {dir}")
            dirData = loadData('stromzaehler', dir, dt.now(), numberOfWeeks)
            if dirData is not None:
                data.append(dirData)
                if dir == "181":
                    zusatz = " HT"
                else:
                    zusatz = ' NT'
                names.append("kWh " + dir + zusatz)
                print(f"{names=}")
            else:
                pass

    #print("ergänze eine total zeile")
    names.append("kWh Total")
    data.append(data[0].copy())        # duplicate first list item
    # in der neuen liste summiere die werte von NT und HT
    data[2]['wert'] = data[0]['wert'] + data[1]['wert']

    # ...und die differenzwerte zum vortag
    data[2]['diffW'] = data[0]['diffW'] + data[1]['diffW']

    names.append("kWh täglich")
    names.append("Betriebsstunden Wärmepumpe")
    names.append("Temperaturbereich")

    # show multiple scatter charts
    #print(f"make subplots {len(names)=}")
    fig = make_subplots(rows=6, cols=1,
                        subplot_titles=(names),
                        shared_xaxes=True)

    for i in range(3):
        # NT, HT, Total
        fig.add_trace({'x': data[0].zeit,
                       'y': data[i].wert,
                       'type': 'scatter',
                       'line': go.scatter.Line(color=linecolors['kWh'][i])},
                       i+1,1)


    # zusätzliches bar chart für die täglichen differenzen im total-bereich
    fig.add_trace(go.Bar(x=data[0].zeit,
                         y=data[2].diffW,
                         marker={'color':"red"},
                         text=data[2].diffW,
                         textposition="auto",
                         textfont=dict(
                             family="Arial Black",
                             size=14,
                             color="lightblue")
                         ), 4,1)

    # zusätzliches bar chart für die täglichen differenzen betriebsstunden wärmepumpe
    dfWpStunden = loadWpStunden(numberOfWeeks)
    fig.add_trace(go.Bar(x=dfWpStunden.tag,
                         y=dfWpStunden.diffH,
                         marker={'color':"red"},
                         text=dfWpStunden.diffH,
                         textposition="auto",
                         textfont=dict(
                             family="Arial Black",
                             size=14,
                             color="lightblue")
                         ), 5,1)

    # zusätzlich die täglichen temperaturbereiche mean
    dfTemp = loadDailyTemp(numberOfWeeks)
    fig.add_trace({'x': dfTemp.tag,
                   'y': dfTemp['mean'],
                   'type': 'scatter',
                   'line': go.scatter.Line(color=linecolors['TempMean'], width=2)},
                   6, 1)

    # ... und den bereichsbalken von min/max
    # dazu die x-punkte vorwärts und rückwärts
    # und die y-punkte min vorwärts und max rückwärts
    fig.add_trace(go.Scatter(x=list(dfTemp['tag']) + list(dfTemp['tag'][::-1]),
                   y=list(dfTemp['min']) + list(dfTemp['max'][::-1]),
                   fill='toself',
                   fillcolor='rgba(80,150,80,0.4)',      # transparent
                   line={'color': 'rgb(80,150,80)'},
                   hoverinfo="skip",
                   showlegend= False),
                   6, 1)


    fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color='white',
        showlegend=False
    )

    return fig


def setZaehlerLayout():
    currentTime = dt.now().strftime("%Y-%m-%d %H:%M")
    page = html.Div(
        style={'backgroundColor': colors['background']},
        children=[
            html.Div(children='Wahl der Anzahl Wochen in der Vergangenheit:',
                     style={'margin-top': 10,
                            'textAlign': 'center',
                            'color': colors['slider']}
            ),
            html.Div(dcc.Slider(id='lastXweeks', min=1, max=10, step=1, value=5,
                       marks={i:f'{i-10}' for i in range(10)}),
                        style={'margin-left': 50, 'margin-right': 50}),

            # this id is referenced in the update_graph_live section
            dcc.Graph(id='graphZaehlerEW', style={'margin-left': 50, 'margin-right': 50, 'height': '80vh'}),

            dcc.Interval(id='refreshInterval', interval=30*60*1000, n_intervals=0),

            html.Meta(httpEquiv="refresh", content="900"),
        ])
    return page

layout = setZaehlerLayout()      # ??? caution, only reference the function, do not call it yet with setLayout()
