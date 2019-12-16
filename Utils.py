
import datetime
import json

def ShowDayNotOverview(show_this_day_timestamp,show_overview_timestamp) :
    thisDayWasPressed = (show_this_day_timestamp != None)
    overviewNeverPressed = (show_overview_timestamp == None)

    if thisDayWasPressed :
        if overviewNeverPressed :
            return True
        if (show_this_day_t > show_overview_t) :
            return True
    
    return False

def GetDayBeginningAndEnd_dt(date) :

    try :
        the_time = datetime.datetime.strptime(date,'%Y-%m-%dT%H:%M:%S')
    except ValueError :
        the_time = datetime.datetime.strptime(date,'%Y-%m-%d')
    start_time = the_time.strftime('%Y-%m-%dT04:00:00')
    end_time  = (the_time+datetime.timedelta(days=1)).strftime('%Y-%m-%dT10:00:00')

    start_time_dt = datetime.datetime.strptime(start_time,'%Y-%m-%dT%H:%M:%S')
    end_time_dt   = datetime.datetime.strptime(end_time  ,'%Y-%m-%dT%H:%M:%S')

    return start_time_dt,end_time_dt
