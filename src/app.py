# ----------------------------------------------------------------------------
# PYTHON LIBRARIES
# ----------------------------------------------------------------------------
# Dash Framework
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table as dt
import dash_daq as daq
from dash.dependencies import Input, Output, State, ALL, MATCH
from dash.exceptions import PreventUpdate

# import local modules
from config_settings import *
from data_processing import *
from make_components import *
from styling import *

# ----------------------------------------------------------------------------
# Parameters
# ----------------------------------------------------------------------------
file_url_root ='https://api.a2cps.org/files/v2/download/public/system/a2cps.storage.community/reports'
report = 'blood'
mcc_list=[1,2]

blood_dict = load_latest_data(file_url_root, report, mcc_list)
blood_df = bloodjson_to_df(blood_dict, mcc_list)
report_df = clean_blooddata(blood_df)
report_dict = report_df.to_dict('records')

# ----------------------------------------------------------------------------
# APP Settings
# ----------------------------------------------------------------------------

external_stylesheets_list = [dbc.themes.SANDSTONE] #  set any external stylesheets

app = dash.Dash(__name__,
                external_stylesheets=external_stylesheets_list,
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}],
                assets_folder=ASSETS_PATH,
                requests_pathname_prefix=REQUESTS_PATHNAME_PREFIX,
                )

# ----------------------------------------------------------------------------
# Page component Parts
# ----------------------------------------------------------------------------

header = html.Div([
    dcc.Store(id='store-latest',
        data = report_dict
    ),
    dbc.Row([
        dbc.Col([html.H1('A2CPS Blood Draw Report')],width=8),
        dbc.Col([html.Div([
            dcc.Dropdown(
                id='dropdown-date',
                options=[
                    {'label': 'latest', 'value': 'latest'}
                ],
                value='latest'
            ),
        ],style={"float":"right"})],width=3),
    ]),
])

# if report_df.empty:
data_check = ''

def make_content_tabs(report_df):
    content_tabs = html.Div([
        dcc.Tabs(id='tabs_tables', children=[
            dcc.Tab(label='Missing Values', children=[
                html.Div(make_missing(report_df), id='tab_missing'),
            ]),
            dcc.Tab(label='Site Info', children=[
                html.Div(site, id='tab_site'),
            ]),
            dcc.Tab(label='Timing', children=[
                html.Div(timing, id='tab_timing'),
            ]),
            dcc.Tab(label='Hemolysis', children=[
                html.Div(make_hemolysis(report_df), id='tab_hemolysis'),
            ]),
            dcc.Tab(label='Deviations', children=[
                html.Div(deviations, id='tab_deviations'),
            ]),
        ]),
        ])
    return content_tabs

# ----------------------------------------------------------------------------
# DASH APP LAYOUT FUNCTION
# ----------------------------------------------------------------------------

def serve_layout():
    # try:
    page_layout = html.Div([
        dbc.Row([
            dbc.Col(data_check),
        ],style={"margin":"10px"}),
        dbc.Row([
            dbc.Col(header),
        ],style={"margin":"10px"}),
        dbc.Row([
            dbc.Col(make_content_tabs(report_df)),
        ],style={"margin":"10px"}),
    ])
    # except:
    #     page_layout = html.Div(['There has been a problem accessing the data for this application.'])
    return page_layout

app.layout = serve_layout


# ----------------------------------------------------------------------------
# DATA CALLBACKS
# ----------------------------------------------------------------------------

# Add callbacks to respond to user input here

# ----------------------------------------------------------------------------
# RUN APPLICATION
# ----------------------------------------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True)
else:
    server = app.server
