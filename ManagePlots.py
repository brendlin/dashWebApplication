import sys
import numpy as np
import pandas as pd
import plotly
import datetime
import time

import ManageBGActions
from ColorSchemes import ColorScheme

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

def GetSummaryPlots(pd_smbg,start_time_dt,end_time_dt) :

    plots = []

    # Make a copy with [:]
    bgs = pd_smbg[(pd.to_datetime(pd_smbg['deviceTime']) > start_time_dt) & (pd.to_datetime(pd_smbg['deviceTime']) < end_time_dt)][:]
    bgs = bgs.sort_values(by='deviceTime',ascending=True)

    # The "index" needs to be a datetime type, with unit "seconds" for some reason.
    #bgs.index = pd.to_datetime(bgs['deviceTime'], unit='s')
    bgs.index = pd.to_datetime(bgs['deviceTime'])

    # 1-week averages
    avg1 = bgs.resample('7D').mean()

    # 4-week average
    wk4 = bgs.rolling(window='28D',min_periods=80)
    avg4 = wk4.mean()['value'].resample('3D').last()
    rms4 = wk4.std()['value'].resample('3D').last()

    # 17-week average
    wk17 = bgs.rolling(window='119D',min_periods=200)
    avg17 = wk17.mean()['value'].resample('3D').last()
    rms17 = wk17.std()['value'].resample('3D').last()

    conv = 18.01559

    # 17-week average error bars
    plots.append({'x':list(avg17.index) + list(avg17.index)[::-1],
                  'y':list(avg17*conv + rms17*conv) + list(avg17*conv - rms17*conv)[::-1],
                  'type':'scatter','name':'17-wk rolling stdev',
                  'fill':'tozeroy',
                  'fillcolor':ColorScheme.Avg17ErrorBar,
                  'mode':'lines',
                  'line':{'width':0},
                  'legendgroup':'17',
                  })

    # 4-week average error bars
    plots.append({'x':list(avg4.index) + list(avg4.index)[::-1],
                  'y':list(avg4*conv + rms4*conv) + list(avg4*conv - rms4*conv)[::-1],
                  'type':'scatter','name':'4-wk rolling stdev',
                  'fill':'tozeroy',
                  'fillcolor':ColorScheme.Avg4ErrorBar,
                  'mode':'lines',
                  'line':{'width':0},
                  'legendgroup':'4',
                  })

    # 17-week average
    plots.append({'x':avg17.index,'y':avg17*conv,
                  'type':'scatter','name':'17-wk rolling avg',
                  'line':{'color':ColorScheme.Avg17Plot,},
                  'legendgroup':'17',
                  })

    # 4-week average
    plots.append({'x':avg4.index,'y':avg4*conv,
                  'type':'scatter','name':'4-wk rolling avg',
                  'mode':'lines',
                  'line':{'color':ColorScheme.Avg4Plot},
                  'legendgroup':'4',
                  })

    # 1-week average
    plots.append({'x':avg1.index,'y':avg1['value']*conv,
                  'type':'scatter','name':'1-wk avg',
                  'mode':'markers',
                  'marker':{'color':'Black','size':4},
                  })

    return plots


def GetPlotCGM(pd_cgm,start_time_dt,end_time_dt) :

    pd_cgm['Time_dt'] = pd.to_datetime(pd_cgm['Time'])

    # [:] to avoid SettingWithCopyWarning
    cgm_inrange = pd_cgm[:][(pd.to_datetime(pd_cgm['Time']) > start_time_dt) & (pd.to_datetime(pd_cgm['Time']) < end_time_dt)]
    cgm_inrange.sort_values(by=['Time_dt'],inplace=True)

    cgm_plot = {'x': cgm_inrange['Time_dt'],
                'y': np.round(cgm_inrange['Glucose']),
                'type': 'scatter', 'name': 'CGM Readings','mode':'markers',
                'marker':{'color':ColorScheme.CGMData,'size':6},
                'line': {'color':ColorScheme.CGMData, 'width':2}
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
