from BGModel import Settings
import datetime
import sys

def LoadFromJsonData(globals) :

    settings_frame = None
    data = globals['global_df']

    if 'basal' in data.columns :
        settings_frame = data[(data['type'] == 'pumpSettings') & (data['basal'].notnull())]
    else :
        print('Warning: no pump settings are available apparently.',file=sys.stdout)
        return
        
    globals['pd_settings'] = settings_frame
    globals['bwz_settings'] = []

    settings_sensitivity = Settings.UserSetting('Sensitivity')
    settings_ric = Settings.UserSetting('RIC')
    settings_duration = Settings.UserSetting('Duration')
    settings_basal = Settings.UserSetting('Basal')

    last_bas = dict()
    last_sens = dict()
    last_carb = dict()
    last_dur = 0

    for i in reversed(range(len(settings_frame))) :

        #print('checking',settings_frame.iloc[i]['deviceTime'])

        tmp_bas  = settings_frame.iloc[i]['basalSchedules']['standard']
        tmp_sens = settings_frame.iloc[i]['insulinSensitivity']
        tmp_carb = settings_frame.iloc[i]['carbRatio']
        tmp_dur  = settings_frame.iloc[i]['bolus']['calculator']['insulin']['duration']

        if (tmp_bas == last_bas and tmp_sens == last_sens and 
            tmp_carb == last_carb and tmp_dur == last_dur) :
            continue
        else :
            last_bas  = tmp_bas
            last_sens = tmp_sens
            last_carb = tmp_carb
            last_dur  = tmp_dur

        #print('New settings from',settings_frame.iloc[i]['deviceTime'])
        deviceTime = settings_frame.iloc[i]['deviceTime']

        for j in settings_frame.iloc[i]['basalSchedules']['standard'] :
            #print('start:',datetime.timedelta(milliseconds=j['start']),'rate:',round(j['rate'],2))
            timeOfDay_hr = datetime.timedelta(milliseconds=j['start']).total_seconds()/3600.
            settings_basal.AddSettingToSnapshot(deviceTime,timeOfDay_hr,round(j['rate'],2))

        for j in settings_frame.iloc[i]['insulinSensitivity'] :
            #print('start:',datetime.timedelta(milliseconds=j['start']),'amount:',round(j['amount']*18.01559,2))
            timeOfDay_hr = datetime.timedelta(milliseconds=j['start']).total_seconds()/3600.
            settings_sensitivity.AddSettingToSnapshot(deviceTime,timeOfDay_hr,round(j['amount']*18.01559,2))

        for j in settings_frame.iloc[i]['carbRatio'] :
            #print('start:',datetime.timedelta(milliseconds=j['start']),'amount:',round(j['amount'],2))
            timeOfDay_hr = datetime.timedelta(milliseconds=j['start']).total_seconds()/3600.
            settings_ric.AddSettingToSnapshot(deviceTime,timeOfDay_hr,round(j['amount'],2))

        #print('duration:',settings_frame.iloc[i]['bolus']['calculator']['insulin']['duration'])
        settings_duration.AddSettingToSnapshot(deviceTime,0,settings_frame.iloc[i]['bolus']['calculator']['insulin']['duration'])

        the_userprofile = Settings.TrueUserProfile()
        the_userprofile.AddSensitivityFromArrays(settings_sensitivity.latestSettingsSnapshot(),
                                                 settings_ric.latestSettingsSnapshot())
        the_userprofile.AddHourlyGlucoseFromArrays(settings_basal.latestSettingsSnapshot(),
                                                   settings_duration.latestSettingsSnapshot())
        the_userprofile.AddDurationFromArray(settings_duration.latestSettingsSnapshot())
        #the_userprofile.Print()
        globals['bwz_settings'].append(the_userprofile)
        globals['current_setting'] = globals['bwz_settings'][-1]

    #print('settings done.')
    return
