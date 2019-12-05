import sys
import numpy as np
import pandas as pd
import plotly
import datetime
import time

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

        containers.sort(key=lambda x: x.iov_0_utc)

        # basals
        containers += ManageBGActions.GetBasals(globals,start_time_dt,end_time_dt)

        # utc times in 6-minute increments
        x_times_utc = range(int(start_time_dt.timestamp()),int(end_time_dt.timestamp()),int(0.1*3600))
        x_times_datetime = list(datetime.datetime.fromtimestamp(a) for a in x_times_utc)

        toggleLightDark = {'InsulinBolus':True,
                           'Food':True,
                           'LiverBasalGlucose':True,
                           'BasalInsulin':True,
                           }

        prediction_plot = ManageBGActions.GetPredictionPlot(globals,containers,start_time_dt64,end_time_dt64)
        fig.append_trace(prediction_plot,1,1)

        net_delta = None

        for c in reversed(containers) :

            classname = c.__class__.__name__

            if classname == 'BGMeasurement' :
                continue

            if abs(c.getIntegral(start_time_dt.timestamp(),end_time_dt.timestamp(),the_userprofile)) < 5 :
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

            the_color = {'InsulinBolus'     :['#66E066','#99EB99'],
                         'Food'             :['#E06666','#EB9999'],
                         'LiverBasalGlucose':['#FFE066','#FFE066'],
                         'BasalInsulin'     :['#ADC2FF','#ADC2FF'],
                         }.get(classname)[toggleLightDark[classname]]
            toggleLightDark[classname] = not toggleLightDark[classname]

            stackgroup = {'InsulinBolus'     :'Negative',
                          'BasalInsulin'     :'Negative',
                          'LiverBasalGlucose':'Positive',
                          'Food'             :'Positive',
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

            fig.append_trace(tmp_plot,2,1)

        net_line = {'x': x_times_datetime,
                    'y': net_delta,
                    'type':'scatter',
                    'name':'Net '+u"\u0394"+'BG',
                    'mode': 'lines',
                    'line': {'color':'black', 'width':2}
                    }
        fig.append_trace(net_line,2,1)

    # Overview plot - single plot
    else :
        fig = plotly.subplots.make_subplots(rows=1, cols=1,
                                            shared_xaxes=True)
        fig.append_trace(top_plot,1,1)

    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20),
                      paper_bgcolor="LightSteelBlue",
                      )

    return fig
