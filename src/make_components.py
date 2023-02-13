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
            page_size=10,
            style_cell={
                'whitespace':'normal',
                'height':'auto',
            },
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
        dbc.Row([
            dbc.Col([
                html.H3('Missing Blood Draws'),
                dcc.Markdown('''Records without a value in the 'bscp_time_blood_draw' column.'''),
                build_datatable(missing_blood_df,'table_missing_blood'),
            ],width=12),
        ]),
        dbc.Row([
            dbc.Col([
                html.H3('Missing Analyses'),
                dcc.Markdown(''' Records with a value of 1 in any of ['bscp_lav1_not_obt', 'bscp_sample_obtained', 'bscp_paxg_aliq_na'] '''),
                build_datatable(missing_analysis_df,'table_missing_analysis'),
            ],width=12),
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Markdown('''
                    **Missing values:**
                    Flag: Pull complete data for all samples with missing values for any of the variables queried in analyses below including variables relating to whether certain tubes were collected and counts of tubes, timing values, hemolysis levels, and protocol deviations.

                    Purpose: Reach back out to MCC to get missing data filled in if possible.
                        '''
                        ,style={"white-space": "pre"})
            ],width=12),
        ]),
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
                dcc.Markdown(''' Count of records with blood draw data grouped by Site and visit type'''),
                dcc.Graph(figure=blood_site_count_fig,id = 'fig_blood_site_count'),
            ],width=6),
            dbc.Col([

            ],width=6),
        ]),
        dbc.Row([
            dbc.Col([
                html.H4('Percent of samples with Pax Obtained'),
                dcc.Markdown(''' '''),
                dcc.Graph(figure=fig_no_pax_df, id = 'fig_no_pax'),
            ],width=6),
            dbc.Col([
                html.H4('Percent of samples with Buffy Obtained'),
                dcc.Markdown(''' '''),
                dcc.Graph(figure=fig_no_buffy_df, id = 'fig_no_buffy'),
            ],width=6),
        ]),
        dbc.Row([
            dbc.Col([
                html.H4('Percent of samples with Aliquot count >= 5'),
                dcc.Markdown(''' '''),
                dcc.Graph(figure=fig_aliquot_5_df,id = 'fig_aliquot_5'),
            ],width=6),
            dbc.Col([
                html.H4('Percent of samples with at least one Aliquot'),
                dcc.Markdown(''' '''),
                dcc.Graph(figure=fig_aliquot_1_df, id = 'fig_aliquot_1'),
            ],width=6),
        ]),
        html.H4('Blood Draws with missing components'),
        dcc.Markdown(''' Samples with a value in one of ['bscp_paxg_aliq_na', 'bscp_buffycoat_na', 'bscp_aliq_cnt']'''),
        build_datatable(metrics_missing,'table_metrics_missing'),
        html.H4('All Blood Draws'),
        dcc.Markdown(''' Full cleaned data set for all samples with a blood draw (here at this point just for reference. Will likely be removed later.) '''),
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
def time_bar(df):
    df = df.sort_values(by=['Site'])
    fig = px.bar(df, x='Visit', y='Percent', facet_col='Site', barmode='group', color='Site')
    fig.update_xaxes(categoryorder='category descending', title='')
    return fig

def time_hist(df, time_col, range_top):
    hist_df = df[df[time_col] < range_top].sort_values(by=['Site'])
    fig = px.histogram(hist_df, x=time_col, facet_col='Site', color='Site')
    return fig

def make_timing(df):
    blood_drawn, missing_blood_df, missing_analysis_df = missing_blood_draws(df)

    centrifuge_df = pass_threshold(blood_drawn,'time_to_centrifuge_minutes', 30)
    # fig_centrifuge_df = bar_percent_figure(centrifuge_df)
    fig_centrifuge_df = time_bar(centrifuge_df)
    hist_centrifuge = time_hist(blood_drawn, "time_to_centrifuge_minutes", 200)



    freezer_df = pass_threshold(blood_drawn,'time_to_freezer_minutes', 60)
    # fig_freezer_df = bar_percent_figure(freezer_df)
    fig_freezer_df = time_bar(freezer_df)
    hist_freezer = time_hist(blood_drawn, "time_to_freezer_minutes", 200)

    timing = html.Div([
        dbc.Row([
            dbc.Col([
                html.H4('Distribution of centrifuge time'),
                    dcc.Markdown('''Histograms of times below 200.  There are only a few records >200, but they are removed for better display of the more normal values.'''),
                dcc.Graph(figure=hist_centrifuge, id = 'fig_hist_centrifuge'),
                html.H4('Percent of samples to Centrifuge in less than 30 min'),
                dcc.Markdown(''' '''),
                dcc.Graph(figure=fig_centrifuge_df, id = 'fig_centrifuge'),
            ],width=6),
            dbc.Col([
                html.H4('Distribution of freezer time'),
                    dcc.Markdown('''Histograms of times below 200.  There are only a few records >200, but they are removed for better display of the more normal values.'''),
                dcc.Graph(figure=hist_freezer, id = 'fig_hist_freezer'),
                html.H4('Percent of samples to Freezer in less than 30 min'),
                dcc.Markdown(''' '''),
                dcc.Graph(figure=fig_freezer_df, id = 'fig_freezer'),
            ],width=6)
        ]),
        dbc.Row([

        ]),
        dbc.Row([
            dbc.Col([
                html.H4('Records that fail time checks'),
                dcc.Markdown(''' Records flagged as failing the time check criteria.
                 blood_df['time_values_check'] = (blood_df['time_to_centrifuge_minutes'] < blood_df['time_to_freezer_minutes'] ) & (blood_df['time_to_centrifuge_minutes'] <= 30) & (blood_df['time_to_freezer_minutes'] <= 60) '''),
                build_datatable(blood_drawn[~blood_drawn['time_values_check']],'table_time_check_fail'),
                ],width = 12)
        ]),
        dbc.Row([
            dbc.Col([
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
            ],width=12)
        ]),

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
        dcc.Markdown('''Roll up data to count number of records by Site, Visit type and degree of hemolysis (table at end)
        Plot barplots of hemolysis degree data colored by visit and split by site
        '''),

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
        dcc.Markdown(''' Deviation columns for records where bscp_protocol_dev !=0 '''),
        build_datatable(deviations_df,'table_deviations'),
        html.H3('Protocol Deviations: Count'),
        dcc.Markdown('''Count of deviation records rolled up by site, visit type and deviation reason '''),
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
