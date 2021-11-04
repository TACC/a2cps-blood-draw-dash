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
    table = dt.DataTable(
        id=table_id,
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
    )
    return table

# ----------------------------------------------------------------------------
# Missing Data Section
# ----------------------------------------------------------------------------
def make_missing(df):
    missing_blood_df, missing_analysis_df = missing_blood_draws(df)

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

site = dcc.Markdown('''
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

# ----------------------------------------------------------------------------
# Timing
# ----------------------------------------------------------------------------

timing =  dcc.Markdown('''
**Timing Data**
* Barplots of counts of samples by time to centrifuge, faceted by site (I think it is a little too hard to see easily with all sites on the same plot)
* Barplots of counts of samples by time to freezer, faceted by site

* Table with percent of samples by site/timepoint where time to centrifuge <= 30mins
* Table with percent of samples by site/timepoint where time to freezer <= 60mins

Flags: Pull complete data for all samples with time to centrifuge > 30mins OR time to freezer > 60 mins OR time to freezer < time to centrifuge

Purpose: Check that protocols are being followed to ensure high quality blood samples
    '''
    ,style={"white-space": "pre"}),

# ----------------------------------------------------------------------------
# Hemolysis
# ----------------------------------------------------------------------------
def make_hemolysis(df):
    hem_degrees = count_hemolysis_records(df)
    hemolysis = html.Div([
        html.H3('Hemolysis Data'),
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

deviations = dcc.Markdown('''
**Protocol Deviations**
Table of counts of protocol deviations by type, by site/timepoint

Flags: Pull complete data for all samples with any protocol deviation

Purpose: Track protocol issues to allow early intervention if recurring problems are occurring
    '''
    ,style={"white-space": "pre"}),
