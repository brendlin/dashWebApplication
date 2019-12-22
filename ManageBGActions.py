
from BGModel.BGActionClasses import *
import datetime
import time
import pandas as pd

#------------------------------------------------------------------
def GetBasals(basals,the_userprofile,start_time_dt64,end_time_dt64,input_containers) :

    containers = []

    st_oneDayBefore = start_time_dt64 - datetime.timedelta(hours=24)
    et_fourHoursAfter = end_time_dt64 + datetime.timedelta(hours=4)

    basal_atTheTime = basals.getValidSnapshotAtTime(start_time_dt64.strftime('%Y-%m-%dT%H:%M:%S'))
    basal = BasalInsulin(st_oneDayBefore.timestamp(),et_fourHoursAfter.timestamp(),
                         basal_atTheTime, # np.array
                         the_userprofile.InsulinSensitivity, # list of size 48
                         input_containers)

    containers.append(basal)

    # liver basal
    liver_glucose = LiverBasalGlucose()

    containers.append(liver_glucose)

    return containers

#------------------------------------------------------------------
def GetSuspendPlot(the_userprofile,containers,start_time_dt,end_time_dt) :

    ret_plots = []

    for c in reversed(containers) :

        if not c.IsSuspend() :
            continue

        if (c.iov_1_utc < start_time_dt.timestamp()) :
            continue

        timestr = time.strftime("%H:%M",time.localtime(c.iov_0_utc))
        tmp_plot = {'x': [datetime.datetime.fromtimestamp(c.iov_0_utc),datetime.datetime.fromtimestamp(c.iov_1_utc)],
                    'y': [0,0],
                    'type':'scatter',
                    'name':'%s Suspend, %.0f min'%(timestr,(c.iov_1_utc-c.iov_0_utc)/60.),
                    'mode': 'lines',
                    'line': {'color':'black', 'width':100},
                    }
        ret_plots.append(tmp_plot)

    return ret_plots

#------------------------------------------------------------------
def GetDeltaPlots(the_userprofile,containers,start_time_dt64,end_time_dt64) :

    ret_plots = []

    # For the net delta plot
    net_delta = None

    # utc times in 6-minute increments
    x_times_utc = range(int(start_time_dt64.timestamp()),int(end_time_dt64.timestamp()),int(0.1*3600))
    x_times_datetime = list(datetime.datetime.fromtimestamp(a) for a in x_times_utc)

    toggleLightDark = {'InsulinBolus':True,
                       'Food':True,
                       'LiverBasalGlucose':True,
                       'BasalInsulin':True,
                       'LiverFattyGlucose':True,
                       'ExerciseEffect':True,
                       }

    for c in reversed(containers) :

        classname = c.__class__.__name__

        if not hasattr(c,'getIntegral') :
            continue

        if abs(c.getIntegral(start_time_dt64.timestamp(),end_time_dt64.timestamp(),the_userprofile)) < 5 :
            continue

        timestr = time.strftime("%H:%M",time.localtime(c.iov_0_utc))

        title = classname
        if c.IsBolus() :
            title = '%s Insulin, %.1f u (%d mg/dL)'%(timestr,c.insulin,c.getMagnitudeOfBGEffect(the_userprofile))
        if c.IsFood() :
            title = '%s Food, %d g (%d mg/dL)'%(timestr,c.food,c.getMagnitudeOfBGEffect(the_userprofile))
        if c.IsBasalInsulin() :
            title = 'Basal Insulin'
        if c.IsBasalGlucose() :
            title = 'Basal Glucose'
        if c.IsLiverFattyGlucose() :
            title = '%s Fatty event (%.2f%%, %d mg/dL)'%(timestr,c.fractionOfBasal,c.BGEffect)

        the_color = {'InsulinBolus'     :['#66E066','#99EB99'],
                     'Food'             :['#E06666','#EB9999'],
                     'LiverBasalGlucose':['#FFE066','#FFE066'],
                     'BasalInsulin'     :['#ADC2FF','#ADC2FF'],
                     'LiverFattyGlucose':['Orange','Orange'],
                     'ExerciseEffect'   :['Purple','Purple'],
                     }.get(classname)[toggleLightDark[classname]]
        toggleLightDark[classname] = not toggleLightDark[classname]

        stackgroup = {'InsulinBolus'     :'Negative',
                      'BasalInsulin'     :'Negative',
                      'ExerciseEffect'   :'Negative',
                      'LiverBasalGlucose':'Positive',
                      'Food'             :'Positive',
                      'LiverFattyGlucose':'Positive',
                      }.get(classname)

        y_values = np.array(list(c.getBGEffectDerivPerHour(time_ut,the_userprofile) for time_ut in x_times_utc))

        net_delta = y_values if (type(net_delta) == type(None)) else (net_delta + y_values)

        tmp_plot = {'x': x_times_datetime,
                    'y': y_values,
                    'type':'scatter',
                    'fill':'tonexty',
                    'name':title,
                    'stackgroup':stackgroup,
                    'mode': 'none',
                    'fillcolor':the_color,
                    }

        ret_plots.append(tmp_plot)

    net_line = {'x': x_times_datetime,
                'y': net_delta,
                'type':'scatter',
                'name':'Net '+u"\u0394"+'BG',
                'mode': 'lines',
                'line': {'color':'black', 'width':2}
                }
    ret_plots.append(net_line)

    return ret_plots

#------------------------------------------------------------------
def GetPredictionPlot(the_userprofile,containers,start_time_dt64,end_time_dt64) :

    st_relevantEvents = start_time_dt64 - datetime.timedelta(hours=12)
    st_firstBG = min(list((c.iov_0_utc if c.IsMeasurement() else 99999999999 for c in containers)))

    # utc times in 6-minute increments
    delta_sec = int(0.2*3600)
    x_times_utc = np.array(range(int(st_firstBG),int(end_time_dt64.timestamp()),delta_sec))
    x_times_datetime = list(datetime.datetime.fromtimestamp(a) for a in x_times_utc)

    net_integral = None

    # First add up all of the integrals
    for c in containers :

        if not hasattr(c,'getIntegral') :
            continue

        y_values = np.array(list(c.getIntegral(st_relevantEvents.timestamp(),time_ut,the_userprofile) for time_ut in x_times_utc))
        net_integral = y_values if (type(net_integral) == type(None)) else (net_integral + y_values)

    # Next decide where the reset points are (rudimentary for now)
    for c in containers :

        if c.__class__.__name__ != 'BGMeasurement' :
            continue

        index = np.searchsorted(x_times_utc,c.iov_0_utc,side='right')
        heav = np.heaviside(x_times_utc - c.iov_0_utc, 1)
        net_integral = net_integral + (c.const_BG - net_integral[index]) * heav

    tmp_plot = {'x': x_times_datetime,
                'y': net_integral,
                'type':'scatter',
                'name':'prediction',
                'mode': 'lines',
                'line': {'color':'gray','dash':'dash'},
                }

    return tmp_plot

#------------------------------------------------------------------
def FormatTimeString(time_str) :
    return pd.to_datetime(time_str).strftime('%Y-%m-%d %H:%M')

#------------------------------------------------------------------
def GetSettingsIndependentConts_Tablef(pd_smbg,pd_cont,start_time_dt64,end_time_dt64) :

    containers_dictf = []

    st_relevantEvents = start_time_dt64 - datetime.timedelta(hours=12)
    st_oneDayBefore = start_time_dt64 - datetime.timedelta(hours=24)

    # measurement
    bgs = pd_smbg[(pd.to_datetime(pd_smbg['deviceTime']) > st_oneDayBefore) & (pd.to_datetime(pd_smbg['deviceTime']) < end_time_dt64)]
    for i in range(len(bgs)) :

        entry = bgs.iloc[i]
        iov_1 = end_time_dt64.strftime('%Y-%m-%dT%H:%M:%S') if (i==0) else bgs.iloc[i+1]['deviceTime']
        value = int(round(entry['value']*18.01559))

        c = {'class':'BGMeasurement','magnitude':value,'hr':'hr','duration_hr':'-',
             'iov_0_str':FormatTimeString(entry['deviceTime'])}

        containers_dictf.append(c)

        # This will exit after the first measurement before our time of interest
        if pd.to_datetime(bgs.iloc[i]['deviceTime']) < start_time_dt64 :
            break

    # insulin
    insulins = pd_cont[(pd_cont['type'] == 'bolus') & (pd.to_datetime(pd_cont['deviceTime']) > st_relevantEvents) & (pd.to_datetime(pd_cont['deviceTime']) < end_time_dt64)]
    for i in range(len(insulins)) :

        entry = insulins.iloc[i]
        subType = entry['subType']
        deviceTime = FormatTimeString(entry['deviceTime'])
        normal = round(entry['normal'],1)
        extended = round(entry['extended'],1)

        if subType == 'normal' :
            # insulin = InsulinBolus.FromStringDate('2019-02-24T09:00:00',2.0)
            c = {'class':'InsulinBolus','magnitude':normal,'hr':'hr','duration_hr':'profile',
                 'iov_0_str':deviceTime}

        elif subType == 'square' :
            # swb = SquareWaveBolus.FromStringDate('2019-02-24T12:00:00',3,2.0) # hours first
            duration_hr = datetime.timedelta(milliseconds=entry['duration']).total_seconds()/3600.
            c = {'class':'SquareWaveBolus','magnitude':normal,'hr':'hr','duration_hr':duration_hr,
                 'iov_0_str':deviceTime}

        elif subType == 'dual/square' :
            # dual wave bolus: hr, extended, normal
            duration_hr = datetime.timedelta(milliseconds=entry['duration']).total_seconds()/3600.
            c = {'class':'DualWaveBolus','magnitude':'%.1fn/%.1fd'%(normal,extended),
                 'hr':'hr','duration_hr':duration_hr,'iov_0_str':deviceTime}

        else :
            print("Error - this is a bolus, but I do not know the subType.")
            continue

        containers_dictf.append(c)

    foods = pd_cont[(pd_cont['type'] == 'wizard') & (pd.to_datetime(pd_cont['deviceTime']) > st_relevantEvents) & (pd.to_datetime(pd_cont['deviceTime']) < end_time_dt64)]
    for i in range(len(foods)) :
        entry = foods.iloc[i]
        if int(entry['carbInput']) == 0 :
            continue

        c = {'class':'Food','magnitude':entry['carbInput'],'hr':'hr','duration_hr':'profile',
             'iov_0_str':FormatTimeString(entry['deviceTime'])}

        containers_dictf.append(c)

    return containers_dictf

#------------------------------------------------------------------
def GetBasals_Tablef() :

    containers = []

    basal = {'class':'BasalInsulin','magnitude':'-','iov_0_str':'-','duration_hr':'-','hr':''}

    containers.append(basal)

    # liver basal
    liver_glucose = {'class':'LiverBasalGlucose','magnitude':'-','iov_0_str':'-','duration_hr':'-','hr':''}

    containers.append(liver_glucose)

    return containers

#------------------------------------------------------------------
def GetBasalSpecialConts_Tablef(pd_basal,start_time_dt64,end_time_dt64,basal_settings,the_userprofile) :

    containers = []

    st_relevantEvents = start_time_dt64 - datetime.timedelta(hours=12)
    basals = pd_basal[(pd.to_datetime(pd_basal['deviceTime']) > st_relevantEvents) & (pd.to_datetime(pd_basal['deviceTime']) < end_time_dt64)]

    for i in range(len(basals)) :
        entry = basals.iloc[i]
        deviceTime = entry['deviceTime']
        deviceTime_end = entry['deviceTime_end_fixed']

        # suspend
        if entry['percent_fixed'] == 0 :
            c = {'class':'Suspend','iov_0_str':deviceTime,'iov_1_str':deviceTime_end,'hr':'hr','magnitude':0}

        else :
            c = {'class':'TempBasal','iov_0_str':deviceTime,'iov_1_str':deviceTime_end,'hr':'hr','magnitude':entry['percent_fixed']}

        containers.append(c)

    # Merge adjacent temp basals (this is an artifact of how they are saved)
    def MergeTempBasals(conts) :
        for i in range(len(conts)-1) :
            c1 = conts[i]
            c2 = conts[i+1]
            if (not c1['class'] == 'TempBasal') or (not c2['class'] == 'TempBasal') :
                continue
            if c1['magnitude'] != c2['magnitude'] :
                continue

            if c2['iov_1_str'] == c1['iov_0_str'] :
                cmerged = {'class':'TempBasal','iov_0_str':c2['iov_0_str'],'iov_1_str':c1['iov_1_str'],'magnitude':c1['magnitude'],'hr':'hr'}
                conts.pop(i)
                conts.pop(i)
                conts.insert(i,cmerged)
                return True
        return False

    try_merge = True
    while try_merge :
        try_merge = MergeTempBasals(containers)

    fatty_events = []

    for c in containers :

        duration = (pd.to_datetime(c['iov_1_str']) - pd.to_datetime(c['iov_0_str'])).total_seconds()/3600.
        duration = round(duration,2)
        c['duration_hr'] = duration
        del c['iov_1_str'] # we do not want this floating around to avoid ambuguity with (editable) duration
        c['iov_0_str'] = FormatTimeString(c['iov_0_str'])

        # Make a fatty event!
        if c['class'] == 'TempBasal' and float(c['magnitude']) > 1 :

            # Update every 6 minutes... same as in BGActionClasses
            time_step_hr = 0.1
            time_hr = 0
            BGEffect = 0
            while time_hr < c['duration_hr'] :

                time_hr += time_step_hr
                # sensitivity setting at time
                insulin_sensi = the_userprofile.getInsulinSensitivityHrMidnight(time_hr)

                # basal setting at time
                bolus_val = basal_settings.GetLatestSettingAtTime(time_hr)*float(time_step_hr)

                BGEffect += -insulin_sensi*bolus_val*(c['magnitude']-1)

            liver = {'class':'LiverFattyGlucose','duration_hr':c['duration_hr'],'iov_0_str':c['iov_0_str'],'magnitude':BGEffect,'hr':'hr'}
            fatty_events.append(liver)

    for f in fatty_events :
        containers.append(f)

    return containers

#------------------------------------------------------------------
def GetContainers_Tablef(pd_smbg,pd_cont,basals,the_userprofile,start_time_dt,end_time_dt,pd_basal) :
    # containers formatted for the table first!

    containers = []

    # food, measurements, insulin, square-wave, dual-wave
    containers += GetSettingsIndependentConts_Tablef(pd_smbg,pd_cont,start_time_dt,end_time_dt)

    # Get containers to feed into basal
    containers += GetBasalSpecialConts_Tablef(pd_basal,start_time_dt,end_time_dt,basals,the_userprofile)

    # basals
    containers += GetBasals_Tablef()

    return containers
