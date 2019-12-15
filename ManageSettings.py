from BGModel import Settings
import datetime
import sys

def getGenericUserProfile() :

    sensitivity = Settings.UserSetting('Sensitivity')
    ric = Settings.UserSetting('RIC')
    duration = Settings.UserSetting('Duration')
    basal = Settings.UserSetting('Basal')

    the_time = '1970-01-01T00:00:01'

    for s in [sensitivity,ric,duration,basal] :
        s.getOrMakeSettingsSnapshot(the_time)

    sensitivity.AddSettingToSnapshot(the_time,0,60)
    ric.AddSettingToSnapshot(the_time,0,15)
    duration.AddSettingToSnapshot(the_time,0,3)
    basal.AddSettingToSnapshot(the_time,0,1.0)

    the_userprofile = Settings.TrueUserProfile()
    the_userprofile.AddSensitivityFromArrays(sensitivity.latestSettingsSnapshot(),
                                             ric.latestSettingsSnapshot())
    the_userprofile.AddHourlyGlucoseFromArrays(basal.latestSettingsSnapshot(),
                                               duration.latestSettingsSnapshot())
    the_userprofile.AddDurationFromArray(duration.latestSettingsSnapshot())

    return the_userprofile

def LoadFromJsonData(data) :
    # give this function the full data frame.

    settings_frame = None

    if 'basal' in data.columns :
        settings_frame = data[(data['type'] == 'pumpSettings') & (data['basal'].notnull())]
    else :
        print('Warning: no pump settings are available apparently.',file=sys.stdout)
        return
        
    all_profiles = []

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

        all_profiles.append([deviceTime,the_userprofile])

    #print('settings done.')
    return all_profiles, settings_basal
