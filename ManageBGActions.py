
from BGModel.BGActionClasses import *
import datetime
import time

def GetSettingsIndependentContainers(globals,start_time_dt64,end_time_dt64) :

    tag = '%s - %s'%(start_time_dt64.strftime('%Y-%m-%dT%H:%M:%S'),
                     end_time_dt64.strftime('%Y-%m-%dT%H:%M:%S'))

    if tag in globals['containers'].keys() :
        return globals['containers'][tag]

    containers = []

    data = globals['global_df']

    st_relevantEvents = start_time_dt64 - datetime.timedelta(hours=12)
    st_oneDayBefore = start_time_dt64 - datetime.timedelta(hours=24)

    # measurement
    bgs = data[(data['type'] == 'smbg') & ((data['deviceTime_dt'] > st_oneDayBefore) & (data['deviceTime_dt'] < end_time_dt64))]
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
        if bgs.iloc[i]['deviceTime_dt'] < start_time_dt64 :
            break

    # insulin
    insulins = data[(data['type'] == 'bolus') & ((data['deviceTime_dt'] > st_relevantEvents) & (data['deviceTime_dt'] < end_time_dt64))]
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

    foods = data[(data['type'] == 'food') & ((data['deviceTime_dt'] > st_relevantEvents) & (data['deviceTime_dt'] < end_time_dt64))]
    for i in range(len(foods)) :
        entry = foods.iloc[i]

        # food = Food.FromStringDate('2019-02-24T12:00:00',30)
        c = Food.FromStringDate(entry['deviceTime'],entry['carbInput'])

        containers.append(c)

    print('tag:',tag)
    globals['containers'][tag] = containers

    for c in containers :
        print(time.ctime(c.iov_0_utc),c.__class__)

    return globals['containers'][tag]
