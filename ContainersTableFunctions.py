
from dash_table import DataTable
import json
import datetime

columns = [['IsBWZ','IsBWZ'],
           ['class','Event type'],
           ['iov_0_str','Start time'],
           ['duration_hr','Duration'],
           ['hr',''],
           ['magnitude','Value'],
           ]

container_opts = ['Add an event','Food','LiverFattyGlucose','ExerciseEffect']

# Exercise: start time, duration, Magnitude, unit
# Food: start time, ta, Magnitude, unit
# fatty glucose: start time (according to temp basal), duration (according to temp basal), (magnitude) percent (according to temp basal) unit (percent)

style_colors = [{'if': {'filter_query':'{class} eq "BasalInsulin"'},'color':'Blue'},
                {'if': {'filter_query':'{class} eq "LiverFattyGlucose"'},'color':'Orange'},
                {'if': {'filter_query':'{class} eq "BGMeasurement"'},'color':'Gray'},
                {'if': {'filter_query':'{class} eq "TempBasal"'},'color':'Gray'},
                {'if': {'filter_query':'{class} eq "Suspend"'},'color':'Gray'},
                {'if': {'filter_query':'{class} eq "LiverBasalGlucose"'},'color':'Yellow'},
                {'if': {'filter_query':'{class} eq "InsulinBolus"'},'color':'Green'},
                {'if': {'filter_query':'{class} eq "Food"'},'color':'Red'},
                ]

container_table = DataTable(id='container-table',
                            columns=[{'name':i[1], 'id':i[0], 'presentation':('dropdown' if i[0] == 'class' else 'input'),'deletable': False,} for i in columns],
                            data=[],
                            editable=True,
                            row_deletable=True,
                            # hide IsBWZ, which you need to see if it should be editable
                            style_cell={'height': '35px'},
                            style_cell_conditional=[{'if': {'column_id': 'IsBWZ'},'display': 'none'},
                                                    {'if': {'column_id': 'class'},'textAlign': 'left'},
                                                    {'if': {'column_id': 'iov_0_str'},'textAlign': 'left'},
                                                    {'if': {'column_id': 'magnitude' },'border_right':'0px'},
                                                    {'if': {'column_id': 'hr' },'border_left':'0px'},
                                                    ],
                            style_data_conditional=[{'if': {'column_id': 'iov_0_str','filter_query': '{class} eq "BasalInsulin"'},'textAlign':'center'},
                                                    {'if': {'column_id': 'iov_0_str','filter_query': '{class} eq "LiverBasalGlucose"'},'textAlign':'center'},
                                                    ] + style_colors,
                            dropdown_conditional=[{'if': {'column_id': 'class',
                                                          'filter_query': '{IsBWZ} eq "0"'},
                                                   'options': list({'label': i, 'value': i} for i in container_opts),
                                                   'clearable':False,
                                                   },
                                                  ],
                            )

container_table_units = DataTable(id='container-table-units',
                                  columns=[{'name':'class','id':'class'},{'name':'', 'id':'unit'}],
                                  data=[],
                                  style_cell={'height': '35px','border_left':'0px','textAlign':'left'},
                                  style_cell_conditional=[{'if': {'column_id': 'class'},'display': 'none'},],
                                  style_data_conditional=style_colors,
                                  )

#------------------------------------------------------------------
def UpdateContainerTable(the_containers_json) :

    out_table = []

    add_an_event = {'iov_0_str':'YYYY-MM-DD HH:MM','iov_1_utc':'','IsBWZ':'0','class':'Add an event','magnitude':'','duration_hr':'','hr':'hr'}

    if not the_containers_json :
        out_table.append(add_an_event)
        return out_table

    containers = the_containers_json.split('$$$')[1:]
    the_date = the_containers_json.split('$$$')[0]

    for c in list(json.loads(c) for c in containers) :
        out_table.append(c)

    add_an_event['iov_0_str'] = the_date.replace('BWZ Inputs','')+' 00:00'
    out_table.append(add_an_event)
    return out_table

#------------------------------------------------------------------
def containerToJson(c) :

    ret = dict()
    ret['class'] = c.__class__.__name__
    ret['magnitude'] = '-'
    ret['iov_0_str'] = '-'
    ret['duration_hr'] = '-'

    if hasattr(c,'iov_0_utc') :
        if not c.__class__.__name__ in ['BasalInsulin','LiverBasalGlucose'] :
            ret['iov_0_str'] = datetime.datetime.fromtimestamp(c.iov_0_utc).strftime("%Y-%m-%d %H:%M")

    for i in ['iov_0_utc','iov_1_utc'] :
        if hasattr(c,i) :
            ret[i] = getattr(c,i)
            if c.__class__.__name__ in ['BGMeasurement','BasalInsulin','LiverFattyGlucose','LiverBasalGlucose'] :
                continue
            ret['duration_hr'] = round((c.iov_1_utc-c.iov_0_utc)/3600.,1)
            ret['hr'] = 'hr'

    if hasattr(c,'Ta_tempBasal') :
        ret['duration_hr'] = round(c.Ta_tempBasal,1)
        ret['hr'] = 'hr'

    for i in ['food','const_BG'] :
        if hasattr(c,i) :
            ret[i] = getattr(c,i)
            ret['magnitude'] = getattr(c,i)

    for i in ['insulin'] :
        if hasattr(c,i) :
            ret[i] = round(getattr(c,i),1)
            ret['magnitude'] = ret[i]

    for i in ['factor','fractionOfBasal','basalFactor'] :
        if hasattr(c,i) :
            ret[i] = round(getattr(c,i),2)*100
            ret['magnitude'] = ret[i]

    for i in ['duration_hr','BasalRates','annotation','Ta_tempBasal'] :
        if hasattr(c,i) :
            ret[i] = getattr(c,i)
            if i == 'duration_hr' :
                ret['hr'] = 'hr'

    # square wave bolus
    for i in ['insulin_inst','insulin_square'] :
        if hasattr(c,i) :
            ret[i] = getattr(c,i)
            ret['magnitude'] = '%.1f+%.1f'%(c.insulin_inst,c.insulin_square)

    return json.dumps(ret)
