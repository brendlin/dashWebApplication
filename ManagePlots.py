import sys
import numpy as np
import pandas as pd
import plotly
import datetime
import time

import ManageBGActions

def GetPlotSMBG(pd_smbg,start_time_dt,end_time_dt) :

#     start_time_s = start_time_dt.timestamp()
#     end_time_s   = end_time_dt.timestamp()
#     print('start_time',start_time_dt)
#     print('end_time',end_time_dt)
#     print('start_time',start_time_s)
#     print('end_time',end_time_s)
#     print(pd_smbg[:10],file=sys.stdout)
#     print('first device time:',pd_smbg['deviceTime'].iloc[0],file=sys.stdout)
#     print('first device time:',pd.to_datetime(pd_smbg['deviceTime'].iloc[0]),file=sys.stdout)

    smbg_inrange = pd_smbg[(pd.to_datetime(pd_smbg['deviceTime']) > start_time_dt) & (pd.to_datetime(pd_smbg['deviceTime']) < end_time_dt)]

    smbg_plot = {'x': smbg_inrange['deviceTime'],
                 'y': np.round(smbg_inrange['value']*18.01559),
                 'type': 'scatter', 'name': 'Meter Readings','mode':'markers',
                 'marker':{'color':'#1C2541','size':12},
                 }

    return smbg_plot

def GetPlotCGM(pd_cgm,start_time_dt,end_time_dt) :

    pd_cgm['Time_dt'] = pd.to_datetime(pd_cgm['Time'])

    # [:] to avoid SettingWithCopyWarning
    cgm_inrange = pd_cgm[:][(pd.to_datetime(pd_cgm['Time']) > start_time_dt) & (pd.to_datetime(pd_cgm['Time']) < end_time_dt)]
    cgm_inrange.sort_values(by=['Time_dt'],inplace=True)

    cgm_plot = {'x': cgm_inrange['Time_dt'],
                'y': np.round(cgm_inrange['Glucose']),
                'type': 'scatter', 'name': 'CGM Readings','mode':'markers',
                'marker':{'color':'#77B6EA','size':6},
                'line': {'color':'#77B6EA', 'width':2}
                }

    return cgm_plot

def GetAnalysisPlots(pd_smbg,pd_cont,basals,containers,the_userprofile,start_time_dt,end_time_dt,pd_basal) :

    return_plots = [[],[]]

    # prediction plot
    prediction_plot = ManageBGActions.GetPredictionPlot(the_userprofile,containers,start_time_dt,end_time_dt)
    return_plots[0].append(prediction_plot)

    # suspend (a plot for now)
    suspends = ManageBGActions.GetSuspendPlot(the_userprofile,containers,start_time_dt,end_time_dt)
    for plot in suspends :
        return_plots[1].append(plot)

    # delta plots
    delta_plots = ManageBGActions.GetDeltaPlots(the_userprofile,containers,start_time_dt,end_time_dt)
    for plot in delta_plots :
        return_plots[1].append(plot)

    return return_plots
