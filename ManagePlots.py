import sys
import numpy as np
import pandas as pd
import plotly
import datetime
import time
import json

from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

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
                 'marker':{'color':ColorScheme.MeterData,'size':12},
                 }

    return smbg_plot

def GetSummaryPlots(pd_smbg,start_time_dt,end_time_dt) :

    plots = []

    # Make a copy with [:]
    bgs = pd_smbg[(pd.to_datetime(pd_smbg['deviceTime']) >= start_time_dt) & (pd.to_datetime(pd_smbg['deviceTime']) <= end_time_dt)][:]
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

    # BG measurements from the table:
    return_plots[0].append(ManageBGActions.GetBGMeasurementsFromTable(containers))

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

def doCGMAnalysis(pd_smbg_json,active_profile_json,active_containers_json,analysis_mode,date,basals_json,pd_cont_json,pd_cgm_json,pd_basal_json) :

    if (not pd_cgm_json) or (not pd_smbg_json) :
        return {}

    pd_smbg = pd.read_json(pd_smbg_json)
    pd_smbg = pd_smbg[pd_smbg['value'] < (350/18.01559)]
    pd_smbg = pd_smbg[pd_smbg['value'] > ( 40/18.01559)]

    pd_cgm = pd.read_json(pd_cgm_json)
    pd_cgm['deviceTime'] = pd_cgm['Time']

    pd_smbg['deviceTime_dt'] = pd.to_datetime(pd_smbg['deviceTime'])
    pd_cgm ['deviceTime_dt'] = pd.to_datetime(pd_cgm ['deviceTime'])

    pd_smbg = pd_smbg.sort_values(by='deviceTime_dt',ascending=True)
    pd_cgm  = pd_cgm.sort_values(by='deviceTime_dt',ascending=True)

    # Default is 'backward', which means CGM readings will be earlier than BG (necessary since I usually start eating after fingerstick.)
    pd_merged = pd.merge_asof(pd_smbg,pd_cgm,on='deviceTime_dt',tolerance=pd.Timedelta('15m'),direction='backward')
    pd_merged = pd_merged[pd_merged['Glucose'].notnull()]

    fig = plotly.subplots.make_subplots(rows=2,cols=2,specs=[[{"rowspan": 2},{}],[None,{}]],)
    UpdateLayout(fig)
    fig.update_layout(legend=dict(x=0, y=1,bgcolor=ColorScheme.Transparent,))
    fig.update_layout(margin=dict(l=20, r=20, t=27, b=20))
    fig.update_layout(showlegend=True)

    # Row 1, column 1
    fig.update_xaxes(range=[30,350], row=1, col=1, nticks=7, domain=[0,0.5])
    fig.update_yaxes(range=[30,350], row=1, col=1)
    fig.update_yaxes(title_text="CGM BG (mg/dL)", row=1, col=1, gridcolor='White')
    fig.update_xaxes(title_text="Capillary BG (mg/dL)", row=1, col=1, gridcolor='White')
    fig.update_xaxes(hoverformat='0.0f',row=1,col=1)

    # Row 1, column 2
    fig.update_xaxes(row=1, col=2, gridcolor='White',range=[-1,1])
    fig.update_yaxes(row=1, col=2, gridcolor='White',linecolor='Black',mirror='ticks',rangemode='tozero')

    # Row 2, column 2
    fig.update_xaxes(title_text="(CGM-Capillary)/Capillary", row=2, col=2, gridcolor='White', range=[-1,1],)
    fig.update_yaxes(row=2, col=2, gridcolor='White',linecolor='Black',mirror='ticks',rangemode='tozero',type='log')

    # plus-or-minus 20%
    fig.append_trace({'x':[30,36,350,350,291,30,30],'y':[30,30,291,350,350,36,30],
                      'name':'y = x'+u'\u00B1'+'20%','mode':'lines',
                      'line':{'width':1,'color':'LightGray'},
                      'fillcolor':'LightGray','fill':'tozeroy',},1,1)

    fig.append_trace({'x':[30,350],'y':[30,350],
                      'name':'y = x',
                      'mode':'lines',
                      'line':{'width':1,'color':'Gray'},
                      },1,1)

    # Zones
    fig.append_trace({'x':[50,170,350],'y':[30,145,275],'name':'Zone A','mode':'lines',
                      'line':{'width':1,'color':'Orange'},},1,1)
    fig.append_trace({'x':[30,140,260],'y':[50,170,350],'name':'Zone A','mode':'lines',
                      'line':{'width':1,'color':'Orange'},'showlegend':False,},1,1)
    fig.append_trace({'x':[120,260,350],'y':[30,130,167],'name':'Zone B','mode':'lines',
                      'line':{'width':1,'color':'Red'},},1,1)
    fig.append_trace({'x':[30,50,70,173],'y':[60,80,110,350],'name':'Zone B','mode':'lines',
                      'line':{'width':1,'color':'Red'},'showlegend':False,},1,1)

    pd_merged['finger'] = pd_merged['value']*18.01559

    # Linear fit (turn off for now)
    if False :

        c, stats = np.polynomial.polynomial.polyfit(pd_merged['Glucose'].to_numpy(),
                                                    pd_merged['finger'].to_numpy(),3,full=True)
        x = np.linspace(-100,600,100)
        y = c[0] + x*c[1] + x*x*c[2] + x*x*x*c[3] # + x*x*x*x*c[4] + x*x*x*x*x*c[5]

        c2, stats2 = np.polynomial.polynomial.polyfit(pd_merged['Glucose'].to_numpy(),
                                                      pd_merged['finger'].to_numpy(),5,full=True)
        x2 = np.linspace(-100,600,100)
        y2 = c2[0] + x*c2[1] + x*x*c2[2] + x*x*x*c2[3] + x*x*x*x*c2[4] + x*x*x*x*x*c2[5]

        fig.append_trace({'x':y,'y':x,'type':'scatter','name':'Linear fit',
                          'mode':'lines','line':{'width':2,'color':'Blue'},},1,1)
        fig.append_trace({'x':y2,'y':x2,'type':'scatter','name':'Linear fit','showlegend':False,
                          'mode':'lines','line':{'width':2,'color':'Blue'},},1,1)

    fig.append_trace({'x':pd_merged['finger'],'y':pd_merged['Glucose'],
                      'text':pd_merged['deviceTime_dt'].dt.strftime('%Y-%m-%d %H:%M'),
                      'type':'scatter','name':'Data',
                      'mode':'markers',
                      'marker':{'color':'Black','size':4},
                      },1,1)

    pd_merged['diff'] = (pd_merged['Glucose']-pd_merged['finger'])/(pd_merged['finger'])

    # MARD
    #pd_merged['diff'] = np.absolute(pd_merged['Glucose']-pd_merged['finger'])/(pd_merged['finger'])

    # Histogram (built-in)
    # fig.append_trace(go.Histogram(x= diffs, autobinx=False,
    #                               xbins=dict(start=-1,end=1,size=0.1),
    #                               marker={'color':'LightGray'}),1,2)

    # Histogram (by hand)
    xbin_edges = np.linspace(-1, 1, num=20+1)
    bin_centers = xbin_edges[:-1] + np.diff(xbin_edges) / 2
    shape = (len(xbin_edges)+1,)
    sumw = np.zeros(shape)

    def histBin(diff) :
        return np.searchsorted(xbin_edges,diff,side='right')

    pd_merged['xbin'] = np.vectorize(histBin)(pd_merged['diff'])
    for xbin in pd_merged['xbin'] :
        sumw[xbin] += 1

    mard_plot = {'x':bin_centers,'y':sumw[1:-1],
                 'error_y':dict(type='data', # value of error bar given in data coordinates
                                array=np.sqrt(sumw[1:-1]),
                                visible=True),
                 'type':'scatter','name':'Data',
                 'mode':'markers',
                 'marker':{'color':'Black','size':4},
                 'showlegend':False,
                 }

    sig = np.std(pd_merged['diff'])
    mu = np.mean(pd_merged['diff'])

    def gaussian(x, mu, sig):
        return (1/(sig*np.sqrt(2*np.pi))) * np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))

    data = pd.DataFrame()
    data['x'] = np.linspace(-1, 1, num=100+1) # 5 times more points
    data['y'] = gaussian(data['x'],mu,sig)
    data['y'] = 5*data['y']*(len(pd_merged['diff'])/float(data['y'].sum())) # compensate for 5x more points

    stopAt = 0.5
    gaus_plot = {'x':data[data['y'] > stopAt]['x'],'y':data[data['y'] > stopAt]['y'],
                 'type':'scatter',
                 'mode':'lines',
                 'line':{'width':1,'color':'Blue'},
                 'showlegend':False,
                 #'line_shape':'spline',
                 }

    try :
        from scipy.optimize import curve_fit
        def gauss(x, *p):
            _A, _mu, _sigma = p
            return _A*np.exp(-(x-_mu)**2/(2.*_sigma**2))

        # p0 is the initial guess for the fitting coefficients (A, mu and sigma above)
        p0 = [1., 0., 1.]

        coeff, var_matrix = curve_fit(gauss, bin_centers, sumw[1:-1], p0=p0)
        # Get the fitted curve
        data['fit'] = gauss(data['x'], *coeff)

        gaus_fit = {'x':data[data['fit'] > stopAt]['x'],'y':data[data['fit'] > stopAt]['fit'],
                    'type':'scatter',
                    'mode':'lines',
                    'line':{'width':1,'color':'green'},
                    'showlegend':False,
                    }

        mu = coeff[1]
        sig = coeff[2]
        fig.append_trace(gaus_fit ,1,2)
        fig.append_trace(gaus_fit ,2,2)

    except :
        pass

    # Row 1 Column 2
    fig.append_trace(mard_plot,1,2)
    fig.append_trace(gaus_plot,1,2)
    fig.update_layout(annotations=[go.layout.Annotation(x=0.95,y=0.95,xref="paper",yref="paper",
                                                        text="Mean: %.2f"%(mu),showarrow=False),
                                   go.layout.Annotation(x=0.95,y=0.90,xref="paper",yref="paper",
                                                        text="Stdev: %.2f"%(sig),showarrow=False),
                                   ])

    # Row 2 Column 2
    fig.append_trace(mard_plot,2,2)
    fig.append_trace(gaus_plot,2,2)

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
