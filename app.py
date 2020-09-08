# Import required libraries
import pickle
import copy
import pathlib
import dash
import math
import datetime as dt
import pandas as pd
import os
import numpy as np
from pdb import set_trace as stop
import json


import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html

# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("parsed_data").resolve()


# Multi-dropdown options
#from controls import MUNICIPIOS,  GAL_SUBTYPES
controlsf = 'controls.json'
with open(controlsf, encoding='latin1') as f:
        controls = json.load(f)
MUNICIPIOS = controls['MUNICIPIOS']
GAL_SUBTYPES = controls['GAL_SUBTYPES']

TFlat = 28.27
TFlon = -16.53
TFzoom = 8.
MAPw = 400
MAPh = 400


Intro=["In the atlantic island of Tenerife (Canary Islands), ~80% of the water resources are obtained from the underground, and of these resources"+\
" ~65% come through water galleries (~50% of the total hydric resources). Here we display data on the water flows, locations and other parameters of these galleries "+\
"in the period 1975-2015, together with the demographic and rainfall evolution in the same period, segregated by municipalities. ",html.Br(),html.Br(),
"The data on the galleries has been obtained from ", 
html.A("Consejo Insular de Aguas de Tenerife",href="https://ciatf.maps.arcgis.com/apps/webappviewer/index.html?id=8d42d177780043e89d9824cee2166995"),
".",html.Br(),
"Population data coming from ",
html.A("Instituto Canario de Estadística (ISTAC).",href="www.gobiernodecanarias.org/istac"),html.Br(),
"Rainfall data coming from ",
html.A("Agrocabildo.",href="http://www.agrocabildo.org/analisis_climatico.asp")
]

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width initial-scale=1.0"}]
)
server = app.server

# Create controls
#county_options = [
#    {"label": str(COUNTIES[county]), "value": str(county)} for county in COUNTIES
#]

municipios_options = [
    {"label": municipio, "value": municipio}
    for municipio in MUNICIPIOS
]

#well_type_options = [
#    {"label": str(WELL_TYPES[well_type]), "value": str(well_type)}
#    for well_type in WELL_TYPES
#]

gal_subtype_options = [
    {"label": GAL_SUBTYPES[subtype], "value": subtype}
    for subtype in GAL_SUBTYPES
]

# Load data

galeriaspick = os.path.join(DATA_PATH,'galerias_df.pick')

with open(galeriaspick, 'rb') as f:
    df_galerias = pickle.load(f, encoding='latin1')
f.close()

munipick = os.path.join(DATA_PATH,'municipios_df.pick')
with open(munipick, 'rb') as f:
    df_muni = pickle.load(f, encoding='latin1')
f.close()

munigeojson = os.path.join(DATA_PATH, 'municipios.geojson')
with open(munigeojson) as geofile:
    gj_muni = json.load(geofile)



# Create global chart template
mapbox_access_token = "pk.eyJ1IjoicmF6em9sbGluaSIsImEiOiJja2VlNGppa3gwZDM5MzVudG9pNGY1OWZuIn0.KtjwfHbmre6Qh7ZOL5-djg"


maplayout = dict(
    autosize=True,
    #automargin=True,
    margin=dict(l=0, r=0, b=0, t=0),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
    title="",
    mapbox=dict(
        accesstoken=mapbox_access_token,
        style="dark",
        center=dict(lon=TFlon, lat=TFlat),
        zoom=TFzoom,
    ),
)

YEARS = np.arange(1975,2016,5)
startYear = 2000

# Create app layout
app.layout = html.Div(
    [
        #dcc.Store(id="aggregate_data"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        html.Div(
            [
                html.H1(children="Water Galleries in Tenerife"),
                html.P(
                    id="description",
                    children=Intro
                    ),
            ],
            id="header",
            className = "row flex-display",
            style={"margin-bottom":"25px"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H5(
                            "Filter by Gallery exit Altitude [m]:",
                            className="control_label",
                        ),
                        dcc.RangeSlider(
                            id="alt_slider",
                            min=0,
                            max=2500,
                            value=[0, 2500],
                            className="dcc_control",
                            marks={
                                    str(alt): {
                                        "label": str(alt),
                                        "style": {"color": "#7fafdf"},     
                                    }
                                    for alt in np.arange(0,2500+1,500)
                                    },
                        ),
                        html.H5(
                            "Filter by Municipality / Region:", 
                            className="control_label"
                        ),
                        dcc.RadioItems(
                            id="gal_municipio_selector",
                            options=[
                                {"label": "All ", "value": "all"},
                                {"label": "NW ", "value": "NW"},
                                {"label": "N ", "value": "N"},
                                {"label": "NE ", "value": "NE"},
                                {"label": "E ", "value": "E"},
                                {"label": "SE ", "value": "SE"},
                                {"label": "S ", "value": "S"},
                                {"label": "W ", "value": "W"},
                                {"label": "Customize ", "value": "custom"},
                            ],
                            value="all",
                            labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        ),
                        dcc.Dropdown(
                            id="gal_municipios",
                            options=municipios_options,
                            multi=True,
                            value=MUNICIPIOS,
                            className="dcc_control",
                        ),
                        html.H5("Filter by Gallery Sub-type:", className="control_label"),
                        dcc.RadioItems(
                            id="gal_subtype_selector",
                            options=[
                                {"label": "All ", "value": "all"},
                                {"label": "Customize ", "value": "custom"},
                            ],
                            value="all",
                            labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        ),
                        dcc.Dropdown(
                            id="gal_subtypes",
                            options=gal_subtype_options,
                            multi=True,
                            value=list(GAL_SUBTYPES.keys()),
                            className="dcc_control",
                        ),
                    ],
                    className="pretty_container four columns",
                    id="cross-filter-options",
                ),
                html.Div(
                    [dcc.Graph(id="trends_graphs"),
                    html.P(
                        ["Upper: Population evolution in the period 1975-2015, for the region(s) selected.",
                        html.Br(),
                        "Lower: Evolution in water flow in the same period according to the selections made in "+\
                        "altitude, region(s), and gallery subtype."],
                        ),
                    ],
                    className="pretty_container seven columns",
                    id='trendsGraphContainer'
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                        id="slider-container",
                        children=[
                            html.P(
                                id="slider-text",
                                children="Drag the slider to change the year:",
                            ),
                            dcc.Slider(
                                id="years-slider",
                                min=min(YEARS),
                                max=max(YEARS),
                                value=startYear,
                                step=None,
                                marks={
                                    str(year): {
                                        "label": str(year),
                                        "style": {"color": "#7fafdf"},     
                                    }
                                    for year in YEARS
                                    },
                            ),
                        ],
                ),
            ],
            id="yearslider",
            className = "row flex-display",
            style={"margin-bottom":"25px"},
        ),
        html.Div(
            [
                html.Div(
                    id="bubbles-container",
                    children=[
                        html.H2("Water flow in year {0}".format(startYear),
                            id="bubbles-title",
                        ),
                        dcc.Graph(
                            id="galerias-bubbles",
                            figure=dict(
                                layout=maplayout,
                            ),
                        ),
                        dcc.Checklist(
                            id="lock_selector",
                            options=[{"label": "Lock camera", "value": "locked"}],
                            className="dcc_control",
                            value=[],
                        ),
                        html.P(
                        ["Map of the waterflows of the water galleries on the island."],
                        ),
                    ],
                    className="pretty_container four columns",
                ),
                html.Div(
                        id="pop-container",
                        children=[
                            html.H2("Population in year {0}".format(startYear),
                                id="population-title",
                            ),
                            dcc.Graph(
                                id="pop-chloro",
                                figure=dict(
                                    layout=dict(
                                        style="dark",
                                        height=MAPh, 
                                        width=MAPw,
                                    ),
                                ),
                            ),
                             html.P(
                        ["Map of the population of the municipalities."],
                        ),
                        ],
                    className="pretty_container four columns",    
                ),
                html.Div(
                    [   
                        html.Div(
                            id="pluvio-container",
                            children=[
                                html.H2("Average precipitation [l/m2]",
                                    id="pluvio-title",
                                ),
                                dcc.Graph(
                                    id="slope-pluvio",
                                    figure=dict(
                                        layout=dict(
                                            style="dark",
                                            height=MAPh, 
                                            width=MAPw,
                                        ),
                                    ),
                                )
                            ]
                        ),
                        html.H5(
                                "Select pluvio-map:", 
                                className="control_label"
                        ),
                        dcc.RadioItems(
                            id="pluvio_selector",
                            options=[
                                {"label": "Mean ", "value": "mean"},
                                {"label": "Trend ", "value": "slope"},
                            ],
                            value="mean",
                            labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        ),
                         html.P(
                        ["Rainfall maps: average / trend in the years 1970-2010."],
                        ),
                    ],
                className="pretty_container four columns",
                )
            ],
            className="row flex-display",  
        ),
        html.Div(
            [
                html.Div(
                    id="histo-caudales",
                    children=[
                        html.H2("Water Flow Distribution in year {0}".format(startYear),
                            id="histo-caudales-title",
                        ),
                        dcc.Graph(
                            id="histo-caudales-graph",
                            figure=dict(),
                        ),
                        html.P(
                        ["Distribution of the water flows for the selected galleries in the given year."]),
                    ],
                    className="pretty_container six columns",
                ),
                html.Div(
                        id="altitude",
                        children=[
                            html.H2("W/Flow-Weighted <Altitudes>",
                                id="altitude-title",
                            ),
                            dcc.Graph(
                                id="alt-vs-year",
                                figure=dict(),
                                ),
                            html.P(
                        ["Flow-weighted average altitude of the selected galleries vs. time."]),
                        ],
                    className="pretty_container five columns",    
                ),
            ],
            className="row flex-display",  
        ),
    ],
    id="root",
    style={"display":"flex", "flex-direction": "column"},
)


# Helper functions

def filter_galerias_df(df, gal_subtypes, municipios, alt_range):
    """ 
    """
    
    dff = df[
        df['municipio'].isin(municipios) &
        df['Subtipo'].isin(gal_subtypes) &
        (df['Z']>=alt_range[0]) &
        (df['Z']<=alt_range[1])
    ]

    return dff

def filter_muni_df(df, municipios):
    dff = df[
        df['municipio'].isin(municipios)
    ]
    return dff

# Create callbacks

# Radio -> multi
@app.callback(
    Output("gal_municipios", "value"), [Input("gal_municipio_selector", "value")]
)
def display_status(selector):
    """
    {"label": "All ", "value": "all"},
    {"label": "NW ", "value": "NW"},
    {"label": "N ", "value": "N"},
    {"label": "METRO ", "value": "METRO"},
    {"label": "SE ", "value": "SE"},
    {"label": "S ", "value": "S"},
    {"label": "W ", "value": "W"},
    {"label": "Customize ", "value": "custom"},
    """
    if selector == "all":
        return MUNICIPIOS
    if selector == 'NW':
        return ["BUENAVISTA DEL NORTE", "LOS SILOS", "GARACHICO",
                "EL TANQUE",
                "SAN JUAN DE LA RAMBLA", "ICOD DE LOS VINOS",
                "LA GUANCHA"]
    if selector == 'N':
        return ["LOS REALEJOS", "PUERTO DE LA CRUZ", "LA OROTAVA",
            "SANTA ÚRSULA", "TACORONTE", "EL SAUZAL",
            "LA MATANZA DE ACENTEJO", "LA VICTORIA DE ACENTEJO"]
    if selector == "NE":
        return ["TEGUESTE", "LA LAGUNA", "SANTA CRUZ DE TENERIFE",
                "EL ROSARIO"]
    if selector == "E":
        return ["CANDELARIA", "ARAFO", "GÜÍMAR"]
    if selector == "SE":
        return ["FASNIA", "ARICO", "GRANADILLA"]
    if selector == "S":
        return ["SAN MIGUEL DE ABONA", "VILAFLOR", "ARONA", "ADEJE"]
    if selector == "W":
        return ["GUÍA DE ISORA", "SANTIAGO DEL TEIDE"]
    return []

# Radio -> multi
@app.callback(Output("gal_subtypes", "value"), [Input("gal_subtype_selector", "value")])
def display_type(selector):
    if selector == "all":
        return list(GAL_SUBTYPES.keys())
    return []

# @app.callback(
#     Output("aggregate_data", "data"),
#     [
#         Input("gal_subtypes", "value"),
#         Input("municipio_selector", "value"),
#     ],
# )


@app.callback(
    Output("trends_graphs", "figure"),
    [Input("gal_subtypes", "value"),
    Input("gal_municipios", "value"),
    Input("alt_slider", "value")],
)
def plot_trends(gal_subtypes, municipios, alt_range):

    dff_galerias = filter_galerias_df(df_galerias, gal_subtypes, municipios, alt_range)
    dff_muni = filter_muni_df(df_muni, municipios)

    fig = make_subplots(rows=2, cols=1, 
                    shared_xaxes=True, 
                    vertical_spacing=0.1,
                    subplot_titles=['Population','Water Flow'])
    
    caudales = dff_galerias.loc[:,[str(y) for y in YEARS]].sum()
    pops = dff_muni.loc[:,[str(y) for y in YEARS]].sum()

    fig.add_trace(go.Scatter(x=YEARS, y=pops,
        name="pop."),
        row=1, col=1)


    fig.add_trace(go.Scatter(x=YEARS, y=caudales, 
        name="w.flow, l/s"),
        row=2, col=1)

    fig.update_yaxes(title_text='[people]',row=1,col=1)
    fig.update_xaxes(title_text='Year',row=2,col=1)
    fig.update_yaxes(title_text='l/s',row=2,col=1)

    fig.update_layout(height=500, width=800)
    fig.update_layout(margin={"r":25,"t":25,"l":50,"b":25})

    return fig

@app.callback(Output("bubbles-title", "children"), [Input("years-slider", "value")])
def update_map_title(year):
    return "Water flow in year {0}".format(year)

@app.callback(
    Output("galerias-bubbles", "figure"),
    [
        Input("years-slider", "value"),
        Input("gal_subtypes", "value"),
        Input("gal_municipios", "value"),
        Input("alt_slider", "value")
    ],
    [State("lock_selector", "value"), State("galerias-bubbles", "relayoutData")],
)
def display_map1(year, gal_subtypes, municipios, alt_range,
    selector, main_graph_layout): #, gal_subtypes, municipio):

    dff_galerias = filter_galerias_df(df_galerias, gal_subtypes, municipios, alt_range)

    fig = px.scatter_mapbox(dff_galerias, lat="Lat", lon="Lon", hover_name="NombreObra", 
                        hover_data=["Z", "municipio"],
                        color_discrete_sequence=["cyan"], 
                        size=str(year),
                        zoom=TFzoom, 
                        height=MAPh, 
                        width=MAPw)
    fig.update_layout(mapbox_style="dark", 
        mapbox_accesstoken=mapbox_access_token)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    # relayoutData is None by default, and {'autosize': True} without relayout action
    if main_graph_layout is not None and selector is not None and "locked" in selector:

        if "mapbox.center" in main_graph_layout.keys():
            lon = float(main_graph_layout["mapbox.center"]["lon"])
            lat = float(main_graph_layout["mapbox.center"]["lat"])
            zoom = float(main_graph_layout["mapbox.zoom"])
            maplayout["mapbox"]["center"]["lon"] = lon
            maplayout["mapbox"]["center"]["lat"] = lat
            maplayout["mapbox"]["zoom"] = zoom
            fig.update_layout(maplayout)

    return fig


@app.callback(Output("population-title", "children"), 
    [Input("years-slider", "value")])
def update_map_title(year):
    return "Population in year {0}".format(year)


@app.callback(
    Output("pop-chloro", "figure"),
    [Input("years-slider", "value")],
)
def display_map2(year):

    color = str(year)


    fig = px.choropleth_mapbox(df_muni, 
                           geojson=gj_muni, 
                           locations='municipio',
                           featureidkey="properties.municipio",
                           color=color,
                           color_continuous_scale="Viridis",
                           range_color=(1000, 50000),
                           height=MAPh, 
                           width=MAPw,
                           mapbox_style="carto-positron",
                           zoom=TFzoom, 
                           center = {"lat": TFlat, "lon": TFlon},
                           opacity=0.5,
                           #labels={'unemp':'unemployment rate'}
                          )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    return fig


@app.callback(Output("pluvio-title", "children"), [Input("pluvio_selector", "value")])
def update_map_title(value):
    titles = dict(mean="Average precipitation",
        slope="Trend in Precipitation")

    return titles[value]

@app.callback(
    Output("slope-pluvio", "figure"),
    [Input("pluvio_selector", "value")],
)
def display_map3(pluvio_key):

    layout_pluvio = dict()

    color = dict(mean='MEANPLUVIO_lm2',
        slope='SLOPEPLUVIO_lm2yr')[pluvio_key]

    range_color = [df_muni[color].min(),
                    df_muni[color].max()]


    fig = px.choropleth_mapbox(df_muni, 
                           geojson=gj_muni, 
                           locations='municipio',
                           featureidkey="properties.municipio",
                           color=color,
                           color_continuous_scale="Viridis",
                           range_color=range_color,
                           height=MAPh, 
                           width=MAPw,
                           mapbox_style="carto-positron",
                           zoom=TFzoom, 
                           center = {"lat": TFlat, "lon": TFlon},
                           opacity=0.5,
                           labels={'MEANPLUVIO_lm2':'[l/m2]',
                           'SLOPEPLUVIO_lm2yr':'[l/m2/yr]'}
                          )
    layout_pluvio.update(dict(
        margin={"r":0,"t":0,"l":0,"b":0},
        annotations=[
        dict(
            x=0.25,
            y=0.85,
            ax=0,
            ay=0,
            text="<{1970-2010}>"
        )
    ])
    )

    fig.update_layout(layout_pluvio)


    return fig


@app.callback(Output("histo-caudales-title", "children"), 
    [Input("years-slider", "value")])
def update_map_title(year):
    return "Water Flow Distribution in year {0}".format(year)


@app.callback(
    Output("histo-caudales-graph", "figure"),
    [
    Input("years-slider", "value"),
    Input("gal_subtypes", "value"),
    Input("gal_municipios", "value"),
    Input("alt_slider", "value")],
)
def plot_histo_caudales(year, gal_subtypes, municipios, alt_range):

    
    dff_galerias = filter_galerias_df(df_galerias, gal_subtypes, municipios, alt_range)

    caudales = dff_galerias.loc[:,str(year)].values
    caudales[caudales == 0.] = 0.0001
    logcaudales = np.log10(caudales)
    

    counts, bins = np.histogram(logcaudales, bins=np.arange(-1, 3.2, 0.2))
    bins = 0.5 * (bins[:-1] + bins[1:])

    fig = px.bar(x=bins, y=counts, labels={'x':'log(Water Flow [l/s])', 'y':'count'})
    

    fig.update_layout(height=400, width=600)
    fig.update_layout(margin={"r":25,"t":25,"l":50,"b":25})

    return fig


@app.callback(
    Output("alt-vs-year", "figure"),
    [
    Input("gal_subtypes", "value"),
    Input("gal_municipios", "value")],
)
def plot_alt_vs_year(gal_subtypes, municipios):
    """ """
    
    alt_range = [0., 1.E4] # unconstrained

    dff_galerias = filter_galerias_df(df_galerias, gal_subtypes, municipios, alt_range)
    
    Zs = dff_galerias.loc[:,'Z'].values

    alt_wf = np.zeros_like(YEARS,dtype='float32')

    for i,y in enumerate(YEARS):
        try:
            alt_wf[i] = np.average(Zs,weights=dff_galerias.loc[:,str(y)].values)
        except ZeroDivisionError:
            pass

    
    fig = px.line(x=YEARS, y=alt_wf, 
            labels={'y':'<Altitude [m]>', 'x':'year'})
    fig.update_layout(height=400, width=500,
                margin={"r":25,"t":25,"l":50,"b":25})
                #,
                #plot_bgcolor='rgba(0,0,0,0)')

    return fig


if __name__ == "__main__":
    
    app.run_server(debug=True)

