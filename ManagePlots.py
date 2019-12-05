import sys
import numpy as np
import pandas as pd
import plotly
import datetime

import ManageBGActions

def UpdatePlot(globals,start_time_dt,end_time_dt) :

    start_time_dt64 = pd.to_datetime(start_time_dt)
    end_time_dt64   = pd.to_datetime(end_time_dt)

    print(globals['pd_smbg'][:10],file=sys.stdout)
    print('first device time:',globals['pd_smbg']['deviceTime'].iloc[0],file=sys.stdout)

    smbg = globals['pd_smbg']
    smbg_inrange = smbg[(smbg['deviceTime_dt'] > start_time_dt64) & (smbg['deviceTime_dt'] < end_time_dt64)]

    print('start_time',start_time_dt)
    print('end_time',end_time_dt)

    duration_hr = (end_time_dt - start_time_dt).total_seconds()/3600.

    the_userprofile = globals['current_setting']

    do_analysis = (duration_hr < 48)

    top_plot = {'x': smbg_inrange['deviceTime'],
                'y': np.round(smbg_inrange['value']*18.01559),
                'type': 'scatter', 'name': 'Meter Readings','mode':'markers'
                }

    # Analysis plot - two subplots
    if (do_analysis) :
        fig = plotly.subplots.make_subplots(rows=2, cols=1,
                                            shared_xaxes=True,
                                            vertical_spacing=0.02)
        fig.append_trace(top_plot,1,1)
        fig.update_yaxes(title_text="BG (mg/dL)", row=1, col=1)
        fig.update_yaxes(title_text=u"\u0394"+" BG (mg/dL/hr)", row=2, col=1)
        fig.update_xaxes(range=[start_time_dt, end_time_dt])

        containers = []

        # food, measurements, insulin, square-wave, dual-wave
        containers += ManageBGActions.GetSettingsIndependentContainers(globals,start_time_dt,end_time_dt)

        # basals
        containers += ManageBGActions.GetBasals(globals,start_time_dt,end_time_dt)

        # utc times in 6-minute increments
        x_times_utc = range(int(start_time_dt.timestamp()),int(end_time_dt.timestamp()),int(0.1*3600))
        x_times_datetime = list(datetime.datetime.fromtimestamp(a) for a in x_times_utc)

        for c in reversed(containers) :

            if c.__class__.__name__ == 'BGMeasurement' :
                continue

            if abs(c.getIntegral(start_time_dt.timestamp(),end_time_dt.timestamp(),the_userprofile)) < 5 :
                continue

            title = c.__class__.__name__
            if c.IsBolus() :
                title = 'Insulin, %.1f u (%d mg/dL)'%(c.insulin,c.getMagnitudeOfBGEffect(the_userprofile))
            if c.IsFood() :
                title = 'Food, %d g (%d mg/dL)'%(c.food,c.getMagnitudeOfBGEffect(the_userprofile))
            if c.IsBasalInsulin() :
                title = 'Basal Insulin'

            stackgroup = {'InsulinBolus':'Negative',
                          'BasalInsulin':'Negative',
                          'Food':'Positive',
                          }.get(c.__class__.__name__)

            tmp_plot = {'x': x_times_datetime,
                        'y': list(c.getBGEffectDerivPerHour(time_ut,the_userprofile) for time_ut in x_times_utc),
                        'type':'scatter',
                        'fill':'tonexty',
                        'name':title,
                        'stackgroup':stackgroup,
                        'mode': 'none',
                        }

            fig.append_trace(tmp_plot,2,1)

            #y_food = np.array(list(c.getBGEffectDerivPerHour(time_ut,the_userprofile) for time_ut in x_times_utc))
            #y_basalrates = np.array(list(basal.getBGEffectDerivPerHour(time_ut,the_userprofile) for time_ut in x_times_utc))
            #y_liver = np.array(list(liver_glucose.getBGEffectDerivPerHour(time_ut,the_userprofile) for time_ut in x_times_utc))


    # Overview plot - single plot
    else :
        fig = plotly.subplots.make_subplots(rows=1, cols=1,
                                            shared_xaxes=True)
        fig.append_trace(top_plot,1,1)

    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20),
                      paper_bgcolor="LightSteelBlue",
                      )

    return fig
