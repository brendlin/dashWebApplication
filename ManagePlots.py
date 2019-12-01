import sys
import numpy as np
import pandas as pd

def UpdatePlot(globals,start_time_dt,end_time_dt) :

    start_time_dt64 = pd.to_datetime(start_time_dt)
    end_time_dt64   = pd.to_datetime(end_time_dt)

    print(globals['pd_smbg'][:10],file=sys.stdout)
    print('first device time:',globals['pd_smbg']['deviceTime'].iloc[0],file=sys.stdout)

    smbg = globals['pd_smbg']
    smbg_inrange = smbg[(smbg['deviceTime_dt'] > start_time_dt64) & (smbg['deviceTime_dt'] < end_time_dt64)]

    print('start_time',start_time_dt)
    print('end_time',end_time_dt)

    return {'data': [
            {'x': smbg_inrange['deviceTime'], 'y': np.round(smbg_inrange['value']*18.01559),
             'type': 'scatter', 'name': 'blood-sugar-meter','mode':'markers'
             },
            ],
            'layout': {'title': 'Blood sugar versus time',
                       'xaxis':{'title':'Time','range':[start_time_dt,end_time_dt]},
                       'yaxis':{'title':'Blood sugar (mg/dL)'},
                       },
            }
