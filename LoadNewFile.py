import os
import sys
import pandas as pd
import numpy as np
import base64
import io
import datetime
import math
import time

from .ManageSettings import getGenericUserProfile, LoadFromJsonData

this_path = os.path.dirname(__file__)

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

    generic_profile = ['1970-01-01T00:00:01',getGenericUserProfile()]
    generic_profile_bundled = '$$$'.join([generic_profile[0],generic_profile[1].toJson()])

    if contents is None:
        # Use the default file
        pd_all = pd.read_json(this_path+'/bgData/download.json')
        status = 'Using default file.'

    else :

        status, pd_all = process_input_file(contents, name)

        if 'error' in status :
            return status,None,None,generic_profile_bundled,None,None,None

    # print('updating global_smbg',file=sys.stdout)

    # deviceTime in "datetime"
    #pd_all['deviceTime_dt'] = pd.to_datetime(pd_all['deviceTime'])

    # Subset that has the BG settings
    pd_smbg = pd_all[pd_all['type'] == 'smbg'][['deviceTime','value']]
    #pd_smbg['deviceTime_dt'] = pd.to_datetime(pd_all['deviceTime'])

    # Subset for containers
    columns_to_save = ['deviceTime','type','subType','duration','normal','extended','carbInput','value']
    pd_containers = pd_all[(pd_all['type'] == 'wizard') | (pd_all['type'] == 'bolus')][columns_to_save]

    # Subset for basal
    columns_to_save = ['deviceTime','deliveryType','percent','rate','suppressed','duration']

    # Step 1: Pick out all the basals
    pd_tmp1 = pd_all[(pd_all['type'] == 'basal')][columns_to_save]

    # Step 2: Save only temp, suspend, or entries just after temp, suspend
    # [:] to avoid a SettingWithCopyWarning
    pd_tmp2 = pd_tmp1[:][(pd_tmp1['deliveryType'] == 'temp') | (pd_tmp1['deliveryType'].shift(-1) == 'temp') |
                         (pd_tmp1['deliveryType'] == 'suspend') | (pd_tmp1['deliveryType'].shift(-1) == 'suspend')
                         ]

    def getPercentFixed(deliveryType,percent,rate,suppressed) :
        try :
            if deliveryType == 'suspend' :
                return 0.0
            if not math.isnan(percent) :
                return round(percent,2)
            return round(rate/float(suppressed['rate']),2)
        except TypeError :
            return np.nan

    def getDeviceTimeEndFixed(deviceTime,deviceTime_end,duration) :
        scheduled_end = pd.to_datetime(deviceTime) + datetime.timedelta(milliseconds=duration)
        if type(deviceTime_end) != type('') :
            return scheduled_end.strftime('%Y-%m-%dT%H:%M:%S')
        return min(pd.to_datetime(deviceTime_end),scheduled_end).strftime('%Y-%m-%dT%H:%M:%S')

    # Step 3: Save the end-times of temp and suspend based on this skimmed pd. Save fixed percent.
    pd_tmp2['deviceTime_end'] = pd_tmp2['deviceTime'].shift(1)
    pd_tmp2['percent_fixed'] = np.vectorize(getPercentFixed)(pd_tmp2['deliveryType'],pd_tmp2['percent'],pd_tmp2['rate'],pd_tmp2['suppressed'])
    pd_tmp2['deviceTime_end_fixed'] = np.vectorize(getDeviceTimeEndFixed)(pd_tmp2['deviceTime'],pd_tmp2['deviceTime_end'],pd_tmp2['duration'])

    # Step 4: now keep only temp or suspend
    columns_to_save = ['deviceTime','deviceTime_end_fixed','percent_fixed']
    pd_basal = pd_tmp2[(pd_tmp2['deliveryType'] == 'temp') | (pd_tmp2['deliveryType'] == 'suspend')][columns_to_save]

    # These are classes
    # all_profiles is a list of [date,profile]
    all_profiles, settings_basal = LoadFromJsonData(pd_all)
    all_profiles.insert(0,generic_profile)
    last_profile_bundled = '$$$'.join([all_profiles[-1][0],all_profiles[-1][1].toJson()])

    # ###Name1$$$Profile1###Name2$$$Profile2 ... etc.
    profiles_bundled = '###'.join(list('$$$'.join([profile[0],profile[1].toJson()]) for profile in all_profiles))

    return status, settings_basal.toJson(), profiles_bundled, last_profile_bundled, pd_containers.to_json(), pd_smbg.to_json(), pd_basal.to_json()

#
# For the upload callback (uses process_input_file)
#
def LoadLibreFile(contents, name) :
    text_outputs = []

    if contents is None:
        # Use the default file
        libre_filename = this_path+'/bgData/libre.txt'
        pd_all = pd.read_csv(libre_filename)
        while len(pd_all.columns) == 1 :
            pd_all = pd.read_csv(libre_filename,skiprows=1,sep='\t',lineterminator='\n')
        status = 'Using default libre file.'

    else :

        status, pd_all = process_input_file(contents, name)

        if 'error' in status :
            return status,None

    # Take maximum of historic and scan glucose (avoids Nan)
    pd_all['Glucose'] = pd_all[['Historic Glucose (mg/dL)','Scan Glucose (mg/dL)']].max(axis=1)
    pd_cgm = pd_all[pd_all['Glucose'].notnull()][['Time','Glucose']]

    return status, pd_cgm.to_json()
