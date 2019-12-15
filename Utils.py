
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

def containerToJson(c) :

    if c.IsMeasurement() :
        return json.dumps({'class':'BGMeasurement','iov_0_utc':c.iov_0_utc,'iov_1_utc':c.iov_1_utc,'const_BG':c.const_BG})

    if c.IsBolus() :
        return json.dumps({'class':'InsulinBolus','iov_0_utc':c.iov_0_utc,'insulin':c.insulin})

    if c.IsSquareWaveBolus() :
        return json.dumps({'class':'SquareWaveBolus','iov_0_utc':c.iov_0_utc,'insulin':c.insulin,'duration_hr':c.duration_hr})

    if c.IsDualWaveBolus() :
        return json.dumps({'class':'DualWaveBolus','iov_0_utc':c.iov_0_utc,'insulin_square':c.insulin_square,'insulin_inst':c.insulin_inst,'duration_hr':c.duration_hr})

    if c.IsFood() :
        return json.dumps({'class':'Food','iov_0_utc':c.iov_0_utc,'food':c.food})

    if c.IsBasalGlucose() :
        return json.dumps({'class':'LiverBasalGlucose'})

    # We do not need sensitivities, because we will not spawn new LiverFattyGlucose from this.
    if c.IsBasalInsulin() :
        return json.dumps({'class':'BasalInsulin','iov_0_utc':c.iov_0_utc,'iov_1_utc':c.iov_1_utc,'BasalRates':c.BasalRates})

    if c.IsTempBasal() :
        return json.dumps({'class':'TempBasal','iov_0_utc':c.iov_0_utc,'iov_1_utc':c.iov_1_utc,'basalFactor':c.basalFactor})

    if c.IsSuspend() :
        return json.dumps({'class':'Suspend','iov_0_utc':c.iov_0_utc,'iov_1_utc':c.iov_1_utc})

    if c.IsExercise() :
        return json.dumps({'class':'ExerciseEffect','iov_0_utc':c.iov_0_utc,'iov_1_utc':c.iov_1_utc,'factor':c.factor})

    if c.IsLiverFattyGlucose() :
        return json.dumps({'class':'LiverFattyGlucose','iov_0_utc':c.iov_0_utc,'iov_1_utc':c.iov_1_utc,'BGEffect':c.BGEffect,'Ta_tempBasal':c.Ta_tempBasal,'fractionOfBasal':c.fractionOfBasal})

    if c.IsAnnotation() :
        return json.dumps({'class':'Annotation','iov_0_utc':c.iov_0_utc,'iov_1_utc':c.iov_1_utc,'annotation':c.annotation})

    print('Error - unknown class %s'%(c.__class__.__name__))
    return ''
