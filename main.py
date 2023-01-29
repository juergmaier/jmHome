# renamed repositiory from situationUnterstand to JMHome


from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

from app import app         # pip install flask
import config

# import all pages in the app
from apps import thtUnterstand
from apps import thtKeller
from apps import meaco
from apps import strom
from apps import zaehlerEW

# use brand to set top left item in navbar
# use pills=True and on NavLink active="exact" to show the current activated tab
navbar = dbc.Nav(
    children = [
        dbc.NavbarBrand(" jmHome"),
        dbc.NavItem(dbc.NavLink("Unterstand", active="exact", href="/thtUnterstand"), class_name="ml-2"),
        dbc.NavItem(dbc.NavLink("Keller", active="exact", href="/thtKeller")),
        dbc.NavItem(dbc.NavLink("Meaco", active="exact", href="/meaco")),
        dbc.NavItem(dbc.NavLink("Stromverbrauch", active="exact", href="/strom")),
        dbc.NavItem(dbc.NavLink("Zähler EW", active="exact", href="/zaehlerEW"))
    ], pills=True
)

# embedding the navigation bar
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == "":
        pathname = '/thtUnterstand'      # default value
    print(f"display page {pathname}")
    if pathname == '/thtUnterstand':
        #tht.update_graph_live([600, 3])
        return thtUnterstand.layout
    elif pathname == '/thtKeller':
        return thtKeller.layout
    elif pathname == '/meaco':
        return meaco.layout
    elif pathname == '/strom':
        return strom.layout
    elif pathname == '/zaehlerEW':
        return zaehlerEW.layout
    else:
        return thtUnterstand.layout

if __name__ == '__main__':
    config.setAbsPfadDaten("../data")
#    app.run_server(host='192.168.0.15', debug=True)  # use host='0,0,0,0' to drop limit for localhost
    app.run_server(debug=True)  # use host='0,0,0,0' to drop limit for localhost
