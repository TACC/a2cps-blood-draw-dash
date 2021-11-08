# Libraries
# Data
import pandas as pd # Dataframe manipulations
import math

# Dash App
# from jupyter_dash import JupyterDash # for running in a Jupyter Notebook
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table as dt

# Data Visualization
import plotly.express as px
from data_processing import *
from styling import *

# ----------------------------------------------------------------------------
# CUSTOM FUNCTIONS FOR DASH UI COMPONENTS
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# CUSTOM FUNCTIONS FOR DASH UI COMPONENTS
# ----------------------------------------------------------------------------

def build_datatable(df,table_id):
    table = html.Div([
        dt.DataTable(
            id=table_id,
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            style_table={'overflowX': 'auto'},
            sort_action="native",
            sort_mode="multi",
            page_size=10
        )
        ],style={'margin-bottom':'50px'})
    return table

def bar_percent_figure(fig_df):
    fig = px.bar(fig_df, x='Visit', y='Percent', color='Site', barmode='group')
    fig.update_xaxes(categoryorder='category descending')
    return fig

# ----------------------------------------------------------------------------
# Missing Data Section
# ----------------------------------------------------------------------------

def make_missing(df):
    blood_drawn, missing_blood_df, missing_analysis_df = missing_blood_draws(df)

    missing = html.Div([
        html.H3('Missing Blood Draws'),
        build_datatable(missing_blood_df,'table_missing_blood'),
        html.H3('Missing Analyses'),
        build_datatable(missing_analysis_df,'table_missing_analysis'),
        dcc.Markdown('''
            **Missing values:**
            Flag: Pull complete data for all samples with missing values for any of the variables queried in analyses below including variables relating to whether certain tubes were collected and counts of tubes, timing values, hemolysis levels, and protocol deviations.

            Purpose: Reach back out to MCC to get missing data filled in if possible.
                '''
                ,style={"white-space": "pre"})
        ])
    return missing

# ----------------------------------------------------------------------------
# Sample counts by site
# ----------------------------------------------------------------------------
def make_site(df):
    blood_drawn, missing_blood_df, missing_analysis_df = missing_blood_draws(df)

    # Count by site
    blood_site_count = blood_drawn.groupby(['Site','Visit'])['ID'].count().rename('Count').reset_index()
    blood_site_count_fig = px.bar(blood_site_count, x='Visit', y='Count', color='Site',barmode='group')
    blood_site_count_fig.update_xaxes(categoryorder='category descending')

    # Count by percent
    fig_no_pax_df = bar_percent_figure(metric_obtained(blood_drawn, 'bscp_paxg_aliq_na'))
    fig_no_buffy_df = bar_percent_figure(metric_obtained(blood_drawn, 'bscp_buffycoat_na'))
    fig_aliquot_5_df = bar_percent_figure(aliquot_obtained(blood_drawn, 5))
    fig_aliquot_1_df = bar_percent_figure(aliquot_obtained(blood_drawn, 1))

    # Missing elements
    pax_missing = ~blood_drawn['bscp_paxg_aliq_na'].isna()
    buffy_missing = ~blood_drawn['bscp_buffycoat_na'].isna()
    aliquots_missing = blood_drawn['bscp_aliq_cnt'].isna()
    metrics_missing = blood_drawn[pax_missing | buffy_missing | aliquots_missing]
    move_column_inplace(metrics_missing, 'bscp_buffycoat_na', 4)
    move_column_inplace(metrics_missing, 'bscp_paxg_aliq_na', 4)
    move_column_inplace(metrics_missing, 'bscp_aliq_cnt', 4)

    site = html.Div([
        dbc.Row([
            dbc.Col([
                html.H4('Count by Site'),
                dcc.Graph(figure=blood_site_count_fig,id = 'fig_blood_site_count'),
            ],width=6),
            dbc.Col([

            ],width=6),
        ]),
        dbc.Row([
            dbc.Col([
                html.H4('No Pax'),
                dcc.Graph(figure=fig_no_pax_df, id = 'fig_no_pax'),
            ],width=6),
            dbc.Col([
                html.H4('No Buffy'),
                dcc.Graph(figure=fig_no_buffy_df, id = 'fig_no_buffy'),
            ],width=6),
        ]),
        dbc.Row([
            dbc.Col([
                html.H4('Aliquots: >= 5'),
                dcc.Graph(figure=fig_aliquot_5_df,id = 'fig_aliquot_5'),
            ],width=6),
            dbc.Col([
                html.H4('Aliquots: at least one'),
                dcc.Graph(figure=fig_aliquot_1_df, id = 'fig_aliquot_1'),
            ],width=6),
        ]),
        html.H4('Blood Draws with missing components'),
        build_datatable(metrics_missing,'table_metrics_missing'),
        html.H4('All Blood Draws'),
        build_datatable(blood_drawn,'table_blood'),
        dcc.Markdown('''
        **Sample Counts by Site**
        * Barplot showing counts by site (parallel bars) and by timepoint (groups of bars) – DONE
        * Barplot showing percent of samples by site/timepoint with PaxGene obtained
        * Barplot showing percent of samples by site/timepoint with BuffyCoat obtained
        * Barplot showing percent of samples by site/timepoint with at least one aliquot tube obtained
        * Barplot showing percent of samples by site/timepoint with at least five aliquot tubes obtained
        * Barplot showing distribution of counts of aliquot tubes, faceted by site/timepoint (e.g., num sites rows by num timepoints columns, similar to Aliquots Collected plot from current version, but I think I'd prefer sites on separate panels)

        Flags: Pull complete data for all samples with no PaxGene OR no BuffyCoat OR no aliquot tubes

        Purpose: Track number of samples by site, getting a full picture of the types of tubes collected, percent of samples with adequate data collected for analysis
            '''
            ,style={"white-space": "pre"}),
            ])
    return site
# ----------------------------------------------------------------------------
# Timing
# ----------------------------------------------------------------------------
def make_timing(df):
    timing = html.Div([
        dcc.Markdown('''
    **Timing Data**
    * Barplots of counts of samples by time to centrifuge, faceted by site (I think it is a little too hard to see easily with all sites on the same plot)
    * Barplots of counts of samples by time to freezer, faceted by site

    * Table with percent of samples by site/timepoint where time to centrifuge <= 30mins
    * Table with percent of samples by site/timepoint where time to freezer <= 60mins

    Flags: Pull complete data for all samples with time to centrifuge > 30mins OR time to freezer > 60 mins OR time to freezer < time to centrifuge

    Purpose: Check that protocols are being followed to ensure high quality blood samples
        '''
        ,style={"white-space": "pre"}),
        ])
    return timing
# ----------------------------------------------------------------------------
# Hemolysis
# ----------------------------------------------------------------------------
def make_hemolysis_fig(hem_df, site):
    fig_df = hem_df[hem_df['Screening Site'] == site]
    fig = px.bar(fig_df, x='Hemolysis', y='count', color='Visit', title=site,barmode="group")
    fig.update_xaxes(categoryorder='category ascending')
    return fig

def make_hemolysis(df):
    hem_degrees = count_hemolysis_records(df)

    hemolysis = html.Div([
        html.H3('Hemolysis Data'),
        html.Div([
            dcc.Graph(id='graph'+site, figure = make_hemolysis_fig(hem_degrees, site)) for site in hem_degrees['Screening Site'].unique()
        ]),
        build_datatable(hem_degrees,'table_hem_degrees'),

        dcc.Markdown('''
        **Hemolysis:**

        * Barplots of counts of samples by hemolysis level, faceted by site
        * Table with percent of samples by site/timepoint with hemolysis < 1

        Flags: Pull complete data for all samples with hemolysis >= 1

        Purpose: Get a feeling for quality of blood samples being collected
            '''
            ,style={"white-space": "pre"}),
    ])
    return hemolysis

# ----------------------------------------------------------------------------
# Protcol Deviations
# ----------------------------------------------------------------------------

def make_deviations(df):
    deviations_df = get_deviations(df)
    dev_count = deviations_df.groupby(['Site','Visit','Deviation Reason'])['ID'].count().rename('count').reset_index()
    deviations = html.Div([
        html.H3('Protocol Deviations'),
        build_datatable(deviations_df,'table_deviations'),
        html.H3('Protocol Deviations: Count'),
        build_datatable(dev_count,'table_deviations_count'),
        dcc.Markdown('''
        **Protocol Deviations**
        Table of counts of protocol deviations by type, by site/timepoint

        Flags: Pull complete data for all samples with any protocol deviation

        Purpose: Track protocol issues to allow early intervention if recurring problems are occurring
            '''
            ,style={"white-space": "pre"}),
        ])
    return deviations
