
from BGModel.BGActionClasses import *
import datetime
import time
import pandas as pd

def GetSettingsIndependentContainers(pd_smbg,pd_cont,start_time_dt64,end_time_dt64) :

    tag = '%s - %s'%(start_time_dt64.strftime('%Y-%m-%dT%H:%M:%S'),
                     end_time_dt64.strftime('%Y-%m-%dT%H:%M:%S'))

#     if tag in globals['containers'].keys() :
#         return globals['containers'][tag]

    containers = []

    st_relevantEvents = start_time_dt64 - datetime.timedelta(hours=12)
    st_oneDayBefore = start_time_dt64 - datetime.timedelta(hours=24)

    # measurement
    bgs = pd_smbg[(pd.to_datetime(pd_smbg['deviceTime']) > st_oneDayBefore) & (pd.to_datetime(pd_smbg['deviceTime']) < end_time_dt64)]
    for i in range(len(bgs)) :

        entry = bgs.iloc[i]
        iov_1 = end_time_dt64.strftime('%Y-%m-%dT%H:%M:%S') if (i==0) else bgs.iloc[i+1]['deviceTime']
        value = int(round(entry['value']*18.01559))

        # add BG measurement
        # measurement = BGMeasurement.FromStringDate('2019-02-24T12:00:00','2019-02-24T12:45:00',172)
        c = BGMeasurement.FromStringDate(entry['deviceTime'],iov_1,value)
        # print(time.ctime(c.iov_0_utc),time.ctime(c.iov_1_utc))

        containers.append(c)

        # This will exit after the first measurement before our time of interest
        if pd.to_datetime(bgs.iloc[i]['deviceTime']) < start_time_dt64 :
            break

    # insulin
    insulins = pd_cont[(pd_cont['type'] == 'bolus') & (pd.to_datetime(pd_cont['deviceTime']) > st_relevantEvents) & (pd.to_datetime(pd_cont['deviceTime']) < end_time_dt64)]
    for i in range(len(insulins)) :

        entry = insulins.iloc[i]
        subType = entry['subType']

        if subType == 'normal' :
            # insulin = InsulinBolus.FromStringDate('2019-02-24T09:00:00',2.0)
            c = InsulinBolus.FromStringDate(entry['deviceTime'],entry['normal'])

        elif subType == 'square' :
            # swb = SquareWaveBolus.FromStringDate('2019-02-24T12:00:00',3,2.0) # hours first
            duration_hr = datetime.timedelta(milliseconds=entry['duration']).total_seconds()/3600.
            c = InsulinBolus.FromStringDate(entry['deviceTime'],duration_hr,entry['normal'])

        elif subType == 'dual/square' :
            # dual wave bolus: hr, extended, normal
            duration_hr = datetime.timedelta(milliseconds=entry['duration']).total_seconds()/3600.
            c = DualWaveBolus.FromStringDate(entry['deviceTime'],duration_hr,entry['extended'],entry['normal'])

        else :
            print("Error - this is a bolus, but I do not know the subType.")
            continue

        containers.append(c)

    foods = pd_cont[(pd_cont['type'] == 'wizard') & (pd.to_datetime(pd_cont['deviceTime']) > st_relevantEvents) & (pd.to_datetime(pd_cont['deviceTime']) < end_time_dt64)]
    for i in range(len(foods)) :
        entry = foods.iloc[i]

        # food = Food.FromStringDate('2019-02-24T12:00:00',30)
        c = Food.FromStringDate(entry['deviceTime'],entry['carbInput'])

        containers.append(c)

    # print('tag:',tag)
    # globals['containers'][tag] = containers

    # for c in containers :
    #     print(time.ctime(c.iov_0_utc),c.__class__)

    return containers

#------------------------------------------------------------------
def GetBasals(basals,the_userprofile,start_time_dt64,end_time_dt64,input_containers) :

    containers = []

    st_oneDayBefore = start_time_dt64 - datetime.timedelta(hours=24)

    basal_atTheTime = basals.getValidSnapshotAtTime(start_time_dt64.strftime('%Y-%m-%dT%H:%M:%S'))
    basal = BasalInsulin(st_oneDayBefore.timestamp(),end_time_dt64.timestamp(),
                         basal_atTheTime, # np.array
                         the_userprofile.InsulinSensitivity, # list of size 48
                         input_containers)

    containers.append(basal)

    # liver basal
    liver_glucose = LiverBasalGlucose()

    containers.append(liver_glucose)

    return containers

#------------------------------------------------------------------
def GetBasalSpecialContainers(pd_basal,start_time_dt64,end_time_dt64) :

    containers = []

    st_relevantEvents = start_time_dt64 - datetime.timedelta(hours=12)
    basals = pd_basal[(pd.to_datetime(pd_basal['deviceTime']) > st_relevantEvents) & (pd.to_datetime(pd_basal['deviceTime']) < end_time_dt64)]

    for i in range(len(basals)) :
        entry = basals.iloc[i]
        c = TempBasal.FromStringDate(entry['deviceTime'],entry['deviceTime_end_fixed'],entry['percent_fixed'])
        containers.append(c)

    return containers


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
                     }.get(classname)[toggleLightDark[classname]]
        toggleLightDark[classname] = not toggleLightDark[classname]

        stackgroup = {'InsulinBolus'     :'Negative',
                      'BasalInsulin'     :'Negative',
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
