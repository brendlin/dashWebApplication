import sys
import numpy as np
import pandas as pd
import plotly
import datetime
import time
import json

from dash.exceptions import PreventUpdate

import Utils
from BGModel import Settings
from ColorSchemes import ColorScheme
import ManageBGActions
import ContainersTableFunctions

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

    # 1-week averages (starting Sunday 11:59:59 apparently)
    # The label is misleading, so we offset it by one day to correspond with Monday labeling.
    avg1 = bgs.resample('W-SUN',label='left',loffset='1D').mean()

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


def UpdateLayout(fig) :

    fig.update_yaxes(title_text="BG (mg/dL)", row=1, col=1)
    fig.update_yaxes(title_text=u"\u0394"+" BG (mg/dL/hr)", row=2, col=1)
    fig.update_yaxes(range=[50,300], row=1, col=1)
    fig.update_yaxes(gridcolor='LightGray',mirror='ticks',showline=True,linecolor='Black', row=1, col=1)
    fig.update_yaxes(gridcolor='LightGray',mirror='ticks',showline=True,linecolor='Black', row=2, col=1)
    fig.update_yaxes(hoverformat='0.0f',row=1,col=1)
    fig.update_yaxes(hoverformat='0.0f',row=2,col=1)
    fig.update_xaxes(gridcolor='LightGray',mirror='ticks',showline=True,linecolor='Black')
    fig.update_layout(margin=dict(l=20, r=20, t=27, b=20),paper_bgcolor="White",plot_bgcolor='White')
    fig.update_layout(showlegend=False)

    return

def doOverview(pd_smbg_json,active_profile_json,active_containers_json,analysis_mode,date,basals_json,pd_cont_json,pd_cgm_json,pd_basal_json) :

    pd_smbg = pd.read_json(pd_smbg_json)

    fig = plotly.subplots.make_subplots(rows=1,cols=1,shared_xaxes=True)
    UpdateLayout(fig)

    start_time = pd_smbg['deviceTime'].iloc[-1]
    end_time   = pd_smbg['deviceTime'].iloc[0]

    start_time_dt = datetime.datetime.strptime(start_time,'%Y-%m-%dT%H:%M:%S')
    end_time_dt   = datetime.datetime.strptime(end_time  ,'%Y-%m-%dT%H:%M:%S')

    plots = GetSummaryPlots(pd_smbg,start_time_dt,end_time_dt)

    for plot in plots :
        fig.append_trace(plot,1,1)
    fig.update_layout(showlegend=True)
    fig.update_layout(legend=dict(x=0, y=0,bgcolor=ColorScheme.Transparent,))

    return fig


def doDayPlot(pd_smbg_json,active_profile_json,active_containers_json,analysis_mode,date,basals_json,pd_cont_json,pd_cgm_json,pd_basal_json,isSandbox = False) :

    pd_smbg = pd.read_json(pd_smbg_json)

    if isSandbox :
        start_time_dt = datetime.datetime.strptime(Utils.sandbox_date,'%Y-%m-%dT%H:%M:%S')
        end_time_dt   = datetime.datetime.strptime(Utils.sandbox_date_end,'%Y-%m-%dT%H:%M:%S')

    else :
        start_time_dt,end_time_dt = Utils.GetDayBeginningAndEnd_dt(date)

    fig = plotly.subplots.make_subplots(rows=2, cols=1,shared_xaxes=True,vertical_spacing=0.02)
    UpdateLayout(fig)
    fig.update_xaxes(range=[start_time_dt, end_time_dt])
    fig.update_yaxes(range=[30,350], row=1, col=1)
    #fig.update_layout(transition={'duration': 500})

    # Add the cgm
    if pd_cgm_json :
        pd_cgm = pd.read_json(pd_cgm_json)

        cgm_plot = GetPlotCGM(pd_cgm,start_time_dt,end_time_dt)
        fig.append_trace(cgm_plot,1,1)

    # Add the smbg plot
    if pd_smbg_json :
        smbg_plot = GetPlotSMBG(pd_smbg,start_time_dt,end_time_dt)
        fig.append_trace(smbg_plot,1,1)

    # After this point, we assume we are doing the full analysis.
    pd_cont = pd.read_json(pd_cont_json)
    basals = Settings.UserSetting.fromJson(basals_json)
    active_profile = Settings.TrueUserProfile.fromJson(active_profile_json)
    pd_basal = pd.read_json(pd_basal_json)

    # Add the "good range" bands
    Utils.AddTargetBands(fig)

    # load containers, and check if they line up with the date!
    active_containers_tablef = list(json.loads(c) for c in active_containers_json.split('$$$'))
    for c in active_containers_tablef :
        if (c.get('day_tag',None) and start_time_dt.strftime('%Y-%m-%d') not in c['day_tag']) :
            #print('skipping this update')
            raise PreventUpdate
    active_containers = ContainersTableFunctions.tablefToContainers(active_containers_tablef,date)
    # we already made fatty events, so do not re-make them here!
    active_containers += ManageBGActions.GetBasals(basals,active_profile,start_time_dt,end_time_dt,active_containers)

    for c in active_containers :
        if c.IsExercise() :
            c.LoadContainers(active_containers)

    plots = GetAnalysisPlots(pd_smbg,pd_cont,basals,active_containers,active_profile,start_time_dt,end_time_dt,pd_basal)
    for plot in plots[0] :
        fig.append_trace(plot,1,1)
    for plot in plots[1] :
        fig.append_trace(plot,2,1)

    return fig
