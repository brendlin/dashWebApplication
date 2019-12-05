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

        # prediction plot
        prediction_plot = ManageBGActions.GetPredictionPlot(globals,containers,start_time_dt64,end_time_dt64)
        fig.append_trace(prediction_plot,1,1)

        # delta plots
        delta_plots = ManageBGActions.GetDeltaPlots(globals,containers,start_time_dt64,end_time_dt64)
        for plot in delta_plots :
            fig.append_trace(plot,2,1)

    # Overview plot - single plot
    else :
        fig = plotly.subplots.make_subplots(rows=1, cols=1,
                                            shared_xaxes=True)
        fig.append_trace(top_plot,1,1)

    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20),
                      paper_bgcolor="LightSteelBlue",
                      )

    return fig
