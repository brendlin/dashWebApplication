import sys
import pandas as pd
import numpy as np
import base64
import io
import datetime

import ManageSettings

#
# How we parse the input file contents
#
def process_input_file(contents, filename):

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            pd_all = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            pd_all = pd.read_excel(io.BytesIO(decoded))
        elif 'json' in filename :
            pd_all = pd.read_json(io.BytesIO(decoded))

    except Exception as e:
        print(e,file=sys.stdout)
        return 'There was an error processing this file.', ''

    return 'Using new file, named {}'.format(filename), pd_all

#
# For the upload callback (uses process_input_file)
#
def LoadNewFile(contents, name) :
    text_outputs = []

    min_date = datetime.datetime(1995, 8, 5)
    max_date = datetime.datetime(2017, 9, 19)
    month = datetime.datetime(2017, 8, 5)
    day = str(datetime.datetime(2017, 8, 25, 23, 59, 59))

    if contents is None:
        # Use the default file
        pd_all = pd.read_json('download.json')
        status = 'Using default file.'

    else :

        status, pd_all = process_input_file(contents, name)

        if 'error' in status :
            return status,None,None,min_date,max_date,month,day,None,None

    # print('updating global_smbg',file=sys.stdout)

    # deviceTime in "datetime"
    #pd_all['deviceTime_dt'] = pd.to_datetime(pd_all['deviceTime'])

    # Subset that has the BG settings
    pd_smbg = pd_all[pd_all['type'] == 'smbg'][['deviceTime','value']]
    #pd_smbg['deviceTime_dt'] = pd.to_datetime(pd_all['deviceTime'])

    # Subset for containers
    columns_to_save = ['deviceTime','type','subType','duration','normal','extended','carbInput','value']
    pd_containers = pd_all[(pd_all['type'] == 'wizard') | (pd_all['type'] == 'bolus')][columns_to_save]

    # dates!
    min_date = min(np.array(pd_smbg['deviceTime'],dtype='datetime64'))
    max_date = max(np.array(pd_smbg['deviceTime'],dtype='datetime64'))
    month    = max(np.array(pd_smbg['deviceTime'],dtype='datetime64'))
    day      = max(np.array(pd_smbg['deviceTime'],dtype='datetime64'))

    # These are classes
    all_profiles, settings_basal = ManageSettings.LoadFromJsonData(pd_all)

    # ###Name1$$$Profile1###Name2$$$Profile2 ... etc.
    profiles_bundled = '###'.join(list('$$$'.join([profile[0],profile[1].toJson()]) for profile in all_profiles))

    return status, settings_basal.toJson(), profiles_bundled, min_date, max_date, month, day, pd_containers.to_json(), pd_smbg.to_json()

#
# For the upload callback (uses process_input_file)
#
def LoadLibreFile(contents, name) :
    text_outputs = []

    if contents is None:
        # Use the default file
        pd_all = pd.read_csv('libre.csv')
        while len(pd_all.columns) == 1 :
            pd_all = pd.read_csv('libre.csv',skiprows=1,sep='\t',lineterminator='\n')
        status = 'Using default libre file.'

    else :

        status, pd_all = process_input_file(contents, name)

        if 'error' in status :
            return status,None

    # Take maximum of historic and scan glucose (avoids Nan)
    pd_all['Glucose'] = pd_all[['Historic Glucose (mg/dL)','Scan Glucose (mg/dL)']].max(axis=1)
    pd_cgm = pd_all[pd_all['Glucose'].notnull()][['Time','Glucose']]

    return status, pd_cgm.to_json()
