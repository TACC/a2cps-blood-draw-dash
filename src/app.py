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
local_datafile = 'blood_dict.json'

data_load = load_latest_data(file_url_root, report, mcc_list)
if data_load:
    blood_dict = data_load
    file_source = 'TACC files'
else:
    blood_dict = load_data_file(ASSETS_PATH, local_datafile)
    file_source = 'local files'
blood_df = bloodjson_to_df(blood_dict, mcc_list)

report_df = clean_blooddata(blood_df)
report_dict = report_df.to_dict('records')

sites = list(report_df.sort_values(by=['Site'])['Site'].unique())

source = 'Data Source: ' + file_source

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
        dbc.Col([html.H1('A2CPS Blood Draw Report'), html.H5(source)],width=8),
        dbc.Col([html.Div([
            html.H5('Report Date:'),
            dcc.Dropdown(
                id='dropdown-date',
                options=[
                    {'label': 'latest', 'value': 'latest'}
                ],
                value='latest',
            ),
        ])],width=2),
        dbc.Col([html.Div([
            html.H5('Site:'),
            dcc.Dropdown(
                id='dropdown-site',
                options=[{'label': 'All Sites', 'value': 'all'}] + [{'label': k, 'value': k} for k in sites],
                value='all',
            ),
        ])],width=2),
    ]),
])

def make_content_tabs(report_df):
    content_tabs = html.Div([
        dcc.Tabs(id='tabs_tables', children=[
            dcc.Tab(label='Missing Values', children=[
                html.Div(make_missing(report_df), id='tab_missing'),
            ]),
            dcc.Tab(label='Site Info', children=[
                html.Div(make_site(report_df), id='tab_site'),
            ]),
            dcc.Tab(label='Timing', children=[
                html.Div(make_timing(report_df), id='tab_timing'),
            ]),
            dcc.Tab(label='Hemolysis', children=[
                html.Div(make_hemolysis(report_df), id='tab_hemolysis'),
            ]),
            dcc.Tab(label='Deviations', children=[
                html.Div(make_deviations(report_df), id='tab_deviations'),
            ]),
        ]),
        ])
    return content_tabs

# ----------------------------------------------------------------------------
# DASH APP LAYOUT FUNCTION
# ----------------------------------------------------------------------------

def serve_layout():
    # try:
    dcc.Store(id='report_data'),
    page_layout = html.Div([
        dbc.Row([
            dbc.Col(id='testdiv'),
        ],style={"margin":"10px"}),
        dbc.Row([
            dbc.Col(header),
        ],style={"margin":"10px"}),
        dbc.Row([
            dbc.Col(id='contents_div'),
        ],style={"margin":"10px"}),
    ])
    # except:
    #     page_layout = html.Div(['There has been a problem accessing the data for this application.'])
    return page_layout

app.layout = serve_layout


# ----------------------------------------------------------------------------
# DATA CALLBACKS
# ----------------------------------------------------------------------------

# Allow User to run report for all Sites, or just for one.
@app.callback(Output("contents_div","children"), Input('dropdown-site',"value"))
def set_report_data(site):
    if site == 'all':
        site_df = report_df
    else:
        site_df = report_df[report_df['Site'] == site]
    return make_content_tabs(site_df)

# ----------------------------------------------------------------------------
# RUN APPLICATION
# ----------------------------------------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True)
else:
    server = app.server
