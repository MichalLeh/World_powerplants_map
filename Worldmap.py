import math 
import pandas as pd
import re

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly import offline

df = pd.read_csv("powerplant.csv")
dff = pd.read_csv("plantfuel.csv")

fuelColorDict = {'Hydro':'#0066ff', 'Gas': '#6f7c91', 'Other': '#ececec', 'Oil': '#000000', 'Wind': '#afdde9', 
'Nuclear': '#aa8800', 'Coal': '#666666', 'Solar': '#ffcc00', 'Waste': '#c87137', 'Biomass': '#5fd35f', 
'Wave and Tidal': '#5f8dd3', 'Petcoke': '#918a6f', 'Geothermal': '#ff7f2a', 'Cogeneration': '#d40000', 'Storage': '#8a6f91'}

mapStyleList = ['open-street-map', 'carto-positron', 'carto-darkmatter', 
            'stamen-terrain', 'stamen-toner', 'stamen-watercolor']


# CSS for the main content
CONTENT_STYLE = {
    'margin-left': '26.0%',
    'margin-right': '26.0%',
    'padding': '15px 15p',
}

# CSS style arguments for the sidebar.
SIDEBAR_STYLE = {
    'position': 'fixed',
    'top': 0,
    'left': 0,
    'bottom': 0,
    'width': '20%',
    'padding': '20px 10px',
    'background-color': 'white'
}

# Controls for sidebar
controls = dbc.FormGroup(
    [
        html.P('Fuel menu'),
        dcc.Dropdown
            (
                id="fuel-menu",
                options=
                [
                {'label': fuel, 'value': fuel} for fuel in fuelColorDict
                ],
                value=['Hydro', 'Gas', 'Other', 'Oil', 'Wind', 'Nuclear', 'Coal', 'Solar', 'Waste','Biomass', 'Wave and Tidal', 'Petcoke', 'Geothermal', 'Cogeneration','Storage'],
                multi=True
            ),
        html.P("Countries menu"),
        dcc.Checklist
            (
            id="all-checklist",
            options=[{'label': 'All', 'value': 'All'}],
            value=[]
            ),
        dcc.Dropdown
            (
                id="country-menu",
                options=
                [
                {'label': country, 'value': country} for country in df.country.unique()
                ],
                value = ['Czech Republic'],
                style={"padding": "15px"}, 
                multi=True
            ),
        html.P("Map style"),
        dcc.Dropdown
            (
                id="map-style",
                options=
                [
                {'label': style, 'value': style} for style in mapStyleList
                ],
                value = 'open-street-map',
            ),
        html.P("Powerplant search"),
        dcc.RadioItems
            (
                id="search-type",
                options=[{'label': 'starts with', 'value': 'start'},
                        {'label': 'contains', 'value': 'contains'}],
                value='start',
                labelStyle={"padding": "15px"},
            ),
        dcc.Dropdown(id="search-dropdown"),
        html.Button('Submit', id='submit-val', n_clicks=0),
        html.P("Set capacity [MW]"),
        dcc.Input(id='first-capacity-input', type="number", placeholder="0", value=0),
        dcc.Input(id='second-capacity-input', type="number", placeholder="22500", value=22500),
    ]
)

# Sidebar
sidebar = html.Div(
    [
        controls
    ],
    style=SIDEBAR_STYLE,
)

# Map
row_1 = dbc.FormGroup(
    [
        html.H2('World map of power plants', style={'textAlign': 'center', 'font-family': 'Arial Black', 'padding':'15px'}),
        dcc.Graph
            (
                id='world-map'
            )  
    ]
)

# Dash datatable
row_2 = dbc.Container([
    dbc.Row([
        dbc.Col([
        dash_table.DataTable
            (
                id='table',
                columns = [{"name": i, "id": i, "deletable": True} for i in dff.columns],
                data=dff.to_dict('records'),
                sort_action = 'native',
                filter_action="native", # for example in 'Hydro' column write >=50 >>> table will display countries with more than 49 hydro plants etc.
                style_data = {'minWidth': '100px', 'maxWidth': '300px', 'width': '120px'},
                style_cell = {'textAlign': 'center'},
                style_cell_conditional = [{'if': {'column_id': 'Country'}, 'width': '300px'}],
                style_table = {'height': '300px', 'width': '1100px', 'overflowY': 'auto'},
                style_header={'fontWeight': 'bold'}, fixed_rows={'headers': True, 'data': 0},
            ),
        ])
    ])
    ]
)

content = html.Div(
    [
        row_1,
        html.Br(),
        row_2,
        html.Br()
    ],
    style=CONTENT_STYLE
)

app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}], external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([content, sidebar])

# Powerplant search menu 
@app.callback(
    Output("search-dropdown", "options"),
    [Input("search-type", "value"),
    Input("search-dropdown", "search_value")])
def update_options(searchTypeVar, searchVar):
    df = pd.read_csv("powerplant.csv")
    df = df[['name', 'primary_fuel']]
    
    # define the way of searching for the desired powerplant
    if searchVar:
        if searchTypeVar == "start":
            df = df[df['name'].str.startswith(searchVar)]
        else:
            df = df[df['name'].str.contains(searchVar)]

    # create options with every powerplant's name in given .csv file
    options = [
        {'label': "{} ({})".format(name,fuel), 'value': index} for name, fuel, index in zip(df.name, df.primary_fuel, df.index.values)
        ]

    # search as you type - preddicting the rest of a powerplant's name a user is searching for 
    if not searchVar:
        raise PreventUpdate
    else:
        return [o for o in options if searchVar in o["label"]]

# Enabling/Disabling country dropdown menu   
@app.callback(
    Output("country-menu", "disabled"),
    [Input("all-checklist", "value")]
)
def disable(allVar):
    # if All is checked disable
    if allVar:
        return True

# Display world's powerplant map
@app.callback(
    Output('world-map', 'figure'),
    [Input('fuel-menu', 'value'),
    Input('all-checklist', 'value'),
    Input('country-menu', 'value'),
    Input('map-style', 'value'),
    Input('first-capacity-input', 'value'),
    Input('second-capacity-input', 'value'),
    Input('submit-val', 'n_clicks')
    ], [State('search-dropdown', 'value')]
    )
def updateMap(fuelVar, allVar, countryVar, styleVar, firstCapacityVar, secondCapacityVar, n_clicks, searchVar):
    fig = go.Figure()
    radianList, hoverTextList, fuelColorList = [], [], []
    
    # styleVar comes as a list, it has to be string
    styleVar = str(styleVar).strip('[]')
    
    df = pd.read_csv("powerplant.csv")

    if searchVar is None:  
        lati, longi = 10, 10
        zoom = 1
    else:
        s = int(searchVar)

        # without squeeze it'll fetch data in pandas.Series
        lati = df[['latitude']].iloc[s].squeeze() #df.loc[df["name"] == searchVar, "latitude"].squeeze() 
        longi = df[['longitude']].iloc[s].squeeze() 
        
        # latitude/longitude for Scattermapbox must be one of list, numpy.array or pandas.Series
        mapLati, mapLongi = [], []
        mapLati.append(lati)
        mapLongi.append(longi)

        # <br> - single line break
        hoverText = 'Country: {0} <br>Power plant: {1} <br>Capacity: {2} MW <br>Primary fuel: {3}'.format(df[['country']].iloc[s].squeeze(), df[['name']].iloc[s].squeeze(),
                                                                                        df[['capacity_mw']].iloc[s].squeeze(), df[['primary_fuel']].iloc[s].squeeze())
        fuelColor = fuelColorDict[df[['primary_fuel']].iloc[s].squeeze()]
        radian = math.ceil(math.log10(df[['capacity_mw']].iloc[s].squeeze()+1)*10)
        
        # add single marker on the map
        fig.add_trace(go.Scattermapbox(
        lon = mapLongi, 
        lat = mapLati,
        text = hoverText,
        name='',
        marker = dict(
                size = radian,
                color = fuelColor
                )
            )
        )
        zoom = 11

    # if All is checked append every country
    if allVar:
        countryVar = []
        for country in df.country.unique():
            countryVar.append(country)

    # load data which will displayed on the map based on user's inputs
    df = df.loc[df['country'].isin(countryVar)]
    df = df.loc[df['primary_fuel'].isin(fuelVar)]
    df = df[df['capacity_mw'].between(firstCapacityVar, secondCapacityVar)]  

    # append given data into lists for Scattermapbox
    for countryName, plantName, plantCapacity, plantFuel in zip(df['country'], df['name'], df['capacity_mw'], df['primary_fuel']):
        hoverTextList.append('Country: {0} <br>Power plant: {1} <br>Capacity: {2} MW <br>Primary fuel: {3}'.format(countryName, plantName, plantCapacity, plantFuel))
        fuelColorList.append(fuelColorDict[plantFuel])
        radianList.append(math.ceil(math.log10(plantCapacity+1)*10))
    
    # add markers on the map
    fig.add_trace(go.Scattermapbox(
        lon = df['longitude'],
        lat = df['latitude'],
        text = hoverTextList,
        name='',
        marker = dict(
                size = radianList,
                color = fuelColorList,
            )
        )
    )
    fig.update_layout(
        margin ={'l':0,'t':0,'b':0,'r':0},
        showlegend=False,
        width=1100, height=850,
        mapbox = {
            'center': {'lon': longi, 'lat': lati},
            'style': styleVar,
            'zoom': zoom })

    return fig

if __name__ == '__main__':
    app.run_server(port='8085',debug=True)