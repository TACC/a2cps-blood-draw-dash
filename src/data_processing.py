  # Libraries
# Data
# File Management
import os # Operating system library
import pathlib # file paths
import json
import requests
import math
import numpy as np
import pandas as pd # Dataframe manipulations
import datetime
from datetime import datetime, timedelta


# ----------------------------------------------------------------------------
# FUNCTIONS
# ----------------------------------------------------------------------------

def dict_to_col(df, index_cols, dict_col, new_col_name = 'category', add_col_as_category=True):
    ''' Take a dataframe with index columns and a column containing a dictionary and convert
    the dictionary json into separate columns'''
    new_df = df[index_cols +[dict_col]].copy()
    new_df.dropna(subset=[dict_col], inplace=True)
    new_df.reset_index(inplace=True, drop=True)
    if add_col_as_category:
        new_df[new_col_name] = dict_col
    new_df = pd.concat([new_df, pd.json_normalize(new_df[dict_col])], axis=1)
    return new_df

def move_column_inplace(df, col, pos):
    ''' move a column position in df'''
    col = df.pop(col)
    df.insert(pos, col.name, col)

def calc_stacked_bar(df, flag_col):
    ''' Count and calculate pass/fail percents for columns that use 1 as a flag for failure.
    In this case these are: 'bscp_lav1_not_obt', 'bscp_sample_obtained', 'bscp_paxg_aliq_na'
    '''

    flag_df = df[['MCC','Visit','Screening Site',flag_col]].fillna(0)
    flag_df[flag_col] = flag_df[flag_col].astype(int)
    flag_df_count = flag_df.groupby(['MCC','Visit','Screening Site'])[flag_col].count().rename('count').reset_index()
    flag_df_fail = flag_df.groupby(['MCC','Visit','Screening Site'])[flag_col].sum().rename('fail').reset_index()
    flag_df_all = flag_df_count.merge(flag_df_fail, how='outer', on = ['MCC','Visit','Screening Site'])

    flag_df_all['Collected'] = 100 -100 * flag_df_all['fail'] / flag_df_all['count']
    flag_df_all['Fail'] = 100 - flag_df_all['Collected']

    flag_df_all.drop(columns=['count','fail'], inplace=True)

    flag_df_all = flag_df_all.set_index(['MCC','Visit','Screening Site']).stack().reset_index()
    flag_df_all.columns = ['MCC','Visit','Screening Site','Type','Percentage']

    return flag_df_all

def pass_threshold(blood_drawn_df, metric_col, metric_threshold, fail_over = True):
    # Drop missing rows where metric wasn't collected
    df = blood_drawn_df[~blood_drawn_df[metric_col].isna()]

    # Count metric entries by site
    df_count = df.groupby(['Site','Visit'])['ID'].count().rename('Count').reset_index()

    # Subset records that fail threshold (default is over = fail)
    if fail_over:
        fail_df = df[df[metric_col] >= metric_threshold]
    else:
        fail_df = df[df[metric_col] <= metric_threshold]

    # Count failures by site
    fail_df_count = fail_df.groupby(['Site','Visit'])['ID'].count().rename('Fail').reset_index()

    # Merge counts itnto single data frame
    count_total = df_count.merge(fail_df_count, how='left', on=['Site','Visit']).fillna(0)

    # Calculate Pass percentage
    count_total['Percent'] = 100 * (count_total['Count'] - count_total['Fail']) / count_total['Count']

    return count_total

# ----------------------------------------------------------------------------
# LOAD DATA
# ----------------------------------------------------------------------------

def load_data_file(ASSETS_PATH, filename):
    with open(os.path.join(ASSETS_PATH, filename )) as json_file:
        data_json = json.load(json_file)
    return data_json

def load_latest_data(file_url_root, report, mcc_list):
    data_json = {}
    latest_suffix = report + '-[mcc]-latest.json'
    for mcc in mcc_list:
        json_url = '/'.join([file_url_root, report,latest_suffix.replace('[mcc]',str(mcc))])
        r = requests.get(json_url)
        if r.status_code == 200:
            data_json[mcc] = r.json()
        else:
            print(json_url)
            print(r.status_code)
    return data_json

# ----------------------------------------------------------------------------
# JSON input into Dataframe
# ----------------------------------------------------------------------------

def bloodjson_to_df(json, mcc_list):
    df = pd.DataFrame()
    dict_cols = ['Baseline Visit', '6-Wks Post-Op', '3-Mo Post-Op']
    for mcc in mcc_list:
        if mcc in json.keys():
            m = json[mcc]
        if str(mcc) in json.keys():
            mcc=str(mcc)
            m = json[mcc]
        if m:
            mdf = pd.DataFrame.from_dict(m, orient='index')
            mdf.dropna(subset=['screening_site'], inplace=True)
            mdf.reset_index(inplace=True)
            mdf['MCC'] = mcc
            for c in dict_cols:
                if c in mdf.columns:
                    col_df = dict_to_col(mdf, ['index','MCC','screening_site'], c,'Visit')
                    df = pd.concat([df, col_df])
                    df.reset_index(inplace=True, drop=True)
    return df


# ----------------------------------------------------------------------------
# Clean dataframe
# ----------------------------------------------------------------------------

def clean_blooddata(blood_df):
    # Drop baseline dict, 6 week dict, 3 month dict
    blood_df.drop(['Baseline Visit', '6-Wks Post-Op', '3-Mo Post-Op'], axis=1, inplace=True)

    # move Visit column to beginning of DF
    move_column_inplace(blood_df, 'Visit', 2)

    # Convert numeric columns
    numeric_cols = ['bscp_aliq_cnt','bscp_protocol_dev','bscp_protocol_dev_reason']
    blood_df[numeric_cols] = blood_df[numeric_cols].apply(pd.to_numeric,errors='coerce')

    # Convert datetime columns
    datetime_cols = ['bscp_time_blood_draw','bscp_aliquot_freezer_time','bscp_time_centrifuge']
    blood_df[datetime_cols] = blood_df[datetime_cols].apply(pd.to_datetime,errors='coerce')

    # Add calculated columns
    # Calculate time to freezer: freezer time - blood draw time
    blood_df['time_to_freezer'] = blood_df['bscp_aliquot_freezer_time'] - blood_df['bscp_time_blood_draw']
    blood_df['time_to_freezer_minutes'] = blood_df['time_to_freezer'].dt.components['hours']*60 + blood_df['time_to_freezer'].dt.components['minutes']

    # Calculate time to centrifuge: centrifuge time - blood draw time
    blood_df['time_to_centrifuge'] = blood_df['bscp_time_centrifuge'] - blood_df['bscp_time_blood_draw']
    blood_df['time_to_centrifuge_minutes'] = blood_df['time_to_centrifuge'].dt.components['hours']*60 + blood_df['time_to_centrifuge'].dt.components['minutes']

    # Calculate times exist in correct order
    blood_df['time_values_check'] = (blood_df['time_to_centrifuge_minutes'] < blood_df['time_to_freezer_minutes'] ) & (blood_df['time_to_centrifuge_minutes'] <= 30) & (blood_df['time_to_freezer_minutes'] <= 60)

    # Get 'Site' column that combines MCC and screening site
    blood_df['Site'] = 'MCC' + blood_df['MCC'].astype(str) + ': ' + blood_df['screening_site']

    # Convert Deviation Numeric Values to Text
    deviation_dict = {1:'Unable to obtain blood sample -technical reason',
                      2: 'Unable to obtain blood sample -patient related',
                      3: 'Sample handling/processing error'}
    deviation_df = pd.DataFrame.from_dict(deviation_dict, orient='index')
    deviation_df.reset_index(inplace=True)
    deviation_df.columns = ['bscp_protocol_dev_reason','Deviation Reason']
    blood_df = blood_df.merge(deviation_df, on='bscp_protocol_dev_reason', how='left')

    # Clean column names for more human friendly usage
    rename_dict = {'index':'ID',
                   'screening_site':'Screening Site',
                   'bscp_deg_of_hemolysis':'Hemolysis'}

    # rename index col as ID
    blood_df = blood_df.rename(columns=rename_dict)

    return blood_df

# ----------------------------------------------------------------------------
# MISSING DATA
# ----------------------------------------------------------------------------

def missing_blood_draws(df):
    ## MISSING BLOOD DRAWS
    no_blood_draw = df['bscp_time_blood_draw'].isna()
    missing_blood = df[no_blood_draw].sort_values(by=['MCC','Screening Site','ID'])

    blood_drawn = df[~no_blood_draw]
    missing_analysis_logic = (blood_drawn['bscp_lav1_not_obt'] == '1') | (blood_drawn['bscp_sample_obtained'] == '1') | (blood_drawn['bscp_paxg_aliq_na'] == '1')
    missing_analysis = blood_drawn[missing_analysis_logic]
    return blood_drawn, missing_blood, missing_analysis

# ----------------------------------------------------------------------------
# SITE INFO
# ----------------------------------------------------------------------------

def metric_obtained(blood_drawn_df, metric_col):
    blood_site_count = blood_drawn_df.groupby(['Site','Visit'])['ID'].count().rename('Count').reset_index()

    cols = ['ID', 'Site', 'Visit'] + [metric_col]
    df = blood_drawn_df[cols]
    df = df[~df[metric_col].isna()]
    df_count = df.groupby(['Site','Visit'])['ID'].count().rename('Metric Count').reset_index()

    df_total = blood_site_count.merge(df_count, how='left', on=['Site','Visit']).fillna(0)
    df_total['Percent'] = 100 * (df_total['Count'] - df_total['Metric Count']) / df_total['Count']

    return df_total

def aliquot_obtained(blood_drawn_df, threshold):
    blood_site_count = blood_drawn_df.groupby(['Site','Visit'])['ID'].count().rename('Count').reset_index()

    cols = ['ID', 'Site', 'Visit','bscp_aliq_cnt']
    df = blood_drawn_df[cols].copy()
    df = df.fillna(0)
    df['Threshold'] = df['bscp_aliq_cnt'] >= threshold

    df_count = df[~df['Threshold']].groupby(['Site','Visit'])['ID'].count().rename('Below Threshold').reset_index()

    df_total = blood_site_count.merge(df_count, how='left', on=['Site','Visit']).fillna(0)
    df_total['Percent'] = 100 * (df_total['Count'] - df_total['Below Threshold']) / df_total['Count']

    return df_total

# ----------------------------------------------------------------------------
# Hemolysis
# ----------------------------------------------------------------------------

def count_hemolysis_records(df):
    hem_cols = ['ID', 'MCC', 'Screening Site', 'Visit','Hemolysis']
    hem_df = df[hem_cols].dropna(subset=['Hemolysis'])
    hem_df['Hemolysis'] = hem_df['Hemolysis'].str.replace('.','0.',regex=True)

    hem_count = hem_df.groupby(by = ['MCC','Screening Site', 'Visit','Hemolysis']).count().reset_index().rename(columns={'ID':'count'})

    # Get complete list of possible sites / Hem Degrees with counts
    sites_df = hem_df[['MCC','Screening Site']].drop_duplicates().sort_values(by=['MCC','Screening Site']).reset_index(drop=True)
    hem_degrees = pd.DataFrame({'Hemolysis':hem_df['Hemolysis'].unique()})
    visits = pd.DataFrame({'Visit':hem_df['Visit'].unique()})
    hem_degrees = sites_df.merge(hem_degrees, how='cross').merge(visits, how='cross')

    hem_degrees = hem_degrees.merge(hem_count,how='outer', on=['MCC','Screening Site','Hemolysis', 'Visit'])
    hem_degrees = hem_degrees.fillna(0)

    return hem_degrees


# ----------------------------------------------------------------------------
# Deviations
# ----------------------------------------------------------------------------
def get_deviations(df):
    dev_cols = ['Site','ID','Visit','bscp_protocol_dev','bscp_protocol_dev_reason','Deviation Reason']
    dev = df[dev_cols][df.bscp_protocol_dev !=0]
    return dev
