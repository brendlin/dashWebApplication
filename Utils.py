
import datetime
import json
import plotly.graph_objects as go
from .ColorSchemes import ColorScheme
from BGModel import Settings

# These should be kept const
sandbox_date     = '1970-01-03T04:00:00'
sandbox_date_end = '1970-01-04T10:00:00'

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

def AddTargetBands(fig,min_yellow=80,min_green=100,max_green=150,max_yellow=180) :

    fill_color_green = ColorScheme.TargetBandColorGreen
    fill_color_yellow = ColorScheme.TargetBandColorYellow

    fig.add_shape(go.layout.Shape(
            type="rect",xref="paper",yref="y",
            x0=0,x1=1,y0=min_green,y1=max_green,
            fillcolor=fill_color_green,
            line_width=0,layer="below"))

    fig.add_shape(go.layout.Shape(
            type="rect",xref="paper",yref="y",
            x0=0,x1=1,y0=min_yellow,y1=min_green,
            fillcolor=fill_color_yellow,
            line_width=0,layer="below"))

    fig.add_shape(go.layout.Shape(
            type="rect",xref="paper",yref="y",
            x0=0,x1=1,y0=max_green,y1=max_yellow,
            fillcolor=fill_color_yellow,
            line_width=0,layer="below"))

    return

def WrapUpDayContainers(name,conts_Tablef,basals) :
    # The name, the containers in table format, the basals
    s_conts = '$$$'.join(list(json.dumps(c) for c in conts_Tablef))
    s_basals = basals.toJson()

    wrapped = '###'.join([name,s_conts,s_basals])
    return wrapped

def UnWrapDayContainers(wrapped) :

    name,s_conts,s_basals = wrapped.split('###')

    conts = list(json.loads(c) for c in s_conts.split('$$$'))
    basals = Settings.UserSetting.fromJson(s_basals)

    return name,conts,basals
