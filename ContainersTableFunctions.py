
from dash_table import DataTable
import json
import datetime
import Utils
from BGModel.BGActionClasses import *
from BGModel import Settings
from ColorSchemes import ColorScheme

import ManageSettings

columns = [['IsBWZ','IsBWZ'],
           ['class','Event type'],
           ['iov_0_str','Start time'],
           ['duration_hr','Dur.'],
           ['hr',''],
           ['magnitude','Value'],
           ]

container_opts = ['Add an event','Food','LiverFattyGlucose','ExerciseEffect']
height='35px'

# Exercise: start time, duration, Magnitude, unit
# Food: start time, ta, Magnitude, unit
# fatty glucose: start time (according to temp basal), duration (according to temp basal), (magnitude) percent (according to temp basal) unit (percent)

style_colors = [{'if': {'filter_query':'{class} eq "BasalInsulin"'},'color':ColorScheme.BasalInsulinTxt},
                {'if': {'filter_query':'{class} eq "ExerciseEffect"'},'color':ColorScheme.ExerciseEffectTxt},
                {'if': {'filter_query':'{class} eq "LiverFattyGlucose"'},'color':ColorScheme.LiverFattyGlucoseTxt},
                {'if': {'filter_query':'{class} eq "BGMeasurement"'},'color':'Gray'},
                {'if': {'filter_query':'{class} eq "TempBasal"'},'color':'Gray'},
                {'if': {'filter_query':'{class} eq "Suspend"'},'color':'Gray'},
                {'if': {'filter_query':'{class} eq "LiverBasalGlucose"'},'color':ColorScheme.LiverBasalGlucoseTxt},
                {'if': {'filter_query':'{class} eq "InsulinBolus"'},'color':ColorScheme.InsulinBolusTxt},
                {'if': {'filter_query':'{class} eq "Food"'},'color':ColorScheme.FoodTxt},
                ]

container_table = DataTable(id='container-table-editable',
                            columns=[{'name':i[1], 'id':i[0], 'presentation':('dropdown' if i[0] == 'class' else 'input'),'deletable': False,} for i in columns],
                            data=[],
                            editable=True,
                            # row_deletable=True,
                            # hide IsBWZ, which you need to see if it should be editable
                            style_cell={'height': height,'fontWeight':'bold'},
                            style_cell_conditional=[{'if': {'column_id': 'IsBWZ'},'display': 'none'},
                                                    {'if': {'column_id': 'class'},'textAlign': 'left'},
                                                    {'if': {'column_id': 'iov_0_str'},'textAlign': 'left'},
                                                    {'if': {'column_id': 'magnitude' },'border_right':'0px'},
                                                    {'if': {'column_id': 'hr' },'border_left':'0px'},
                                                    ],
                            style_data_conditional=[{'if': {'column_id': 'iov_0_str','filter_query': '{class} eq "BasalInsulin"'},'textAlign':'center'},
                                                    {'if': {'column_id': 'iov_0_str','filter_query': '{class} eq "LiverBasalGlucose"'},'textAlign':'center'},
                                                    ] + style_colors,
                            # dropdown_conditional has been moved to a callback (see flask_app)
                            )

container_table_fixed = DataTable(id='container-table-fixed',
                                  columns=[{'name':i[1], 'id':i[0], 'presentation':('dropdown' if i[0] == 'class' else 'input'),'deletable': False,} for i in columns],
                                  data=[],
                                  editable=False,
                                  # row_deletable=True,
                                  # hide IsBWZ, which you need to see if it should be editable
                                  style_cell={'height': height,'fontWeight':'bold'},
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

columns_basal = [['ValidFrom','Valid from'],
                 ['time','time'],
                 ['Units','Units'],
                 ]

container_table_basal = DataTable(id='container-table-basal',
                                  columns=[ {'name':i[1], 'id':i[0]} for i in columns_basal],
                                  data=[],
                                  style_cell={'height': height,'textAlign':'right','fontWeight':'bold'},
                                  )

container_table_units = DataTable(id='container-table-editable-units',
                                  columns=[{'name':'class','id':'class'},{'name':'', 'id':'unit'}],
                                  data=[],
                                  style_cell={'height': height,'border_left':'0px','textAlign':'left','fontWeight':'bold'},
                                  style_cell_conditional=[{'if': {'column_id': 'class'},'display': 'none'},],
                                  style_data_conditional=style_colors,
                                  )

container_table_fixed_units = DataTable(id='container-table-fixed-units',
                                        columns=[{'name':'class','id':'class'},{'name':'', 'id':'unit'}],
                                        data=[],
                                        style_cell={'height': height,'border_left':'0px','textAlign':'left','fontWeight':'bold'},
                                        style_cell_conditional=[{'if': {'column_id': 'class'},'display': 'none'},],
                                        style_data_conditional=style_colors,
                                        )

#------------------------------------------------------------------
def UpdateContainerTable(the_containers_json,date) :

    out_table_editable = []
    out_table_fixed = []
    out_table_basals = []

    add_an_event = {'iov_0_str':'YYYY-MM-DD HH:MM','iov_1_utc':'','IsBWZ':'0','class':'Add an event','magnitude':'','duration_hr':'','hr':'hr'}

    if not the_containers_json :
        out_table_editable.append(add_an_event)
        return out_table_editable, out_table_fixed, out_table_basals

    the_date,containers,basals = Utils.UnWrapDayContainers(the_containers_json)
    the_date = the_date.replace('@','').replace('BWZ Inputs','').rstrip()

    fixed_conts = ['BasalInsulin','LiverBasalGlucose','BGMeasurement','InsulinBolus','TempBasal','Suspend']

    hidden = []
    start_time_dt,end_time_dt = Utils.GetDayBeginningAndEnd_dt(date)

    for c in containers :

        iov_0_str = c['iov_0_str'].rstrip('- ')
        hide = iov_0_str and datetime.datetime.strptime(iov_0_str,'%Y-%m-%d %H:%M') < start_time_dt

        # this was prepared for a particular day, so we tag it (important for updating the plot)
        c['day_tag'] = the_date

        if hide :
            hidden.append(c)
        elif c['class'] in fixed_conts :
            out_table_fixed.append(c)
        else :
            out_table_editable.append(c)

    # hide containers that are before the start-time of the day
    if out_table_fixed :
        out_table_fixed[0]['hidden'] = hidden

    add_an_event['iov_0_str'] = ' '.join( (the_date.replace('BWZ Inputs','')+' 04:00').split() )
    out_table_editable.append(add_an_event)

    def sorter(x) :
        if x['class'] == 'BasalInsulin' :
            return 'x'
        if x['class'] == 'LiverBasalGlucose' :
            return 'y'
        if 'Add' in x['class'] :
            return 'z'
        return x['iov_0_str']

    out_table_editable.sort(key=sorter)
    out_table_fixed.sort(key=sorter)

    # In an earlier stage we figured out which settings were relevant for a particular day.
    for b in basals.settings_24h :
        valid_date = datetime.datetime.strptime(b[0],'%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d %H:%M')

        for i in range(len(b[1])) :
            bsub = b[1][i]

            # remove duplicates
            if (i > 0) and bsub[1] == b[1][i-1][1] :
                continue

            time_hr = int(bsub[0])/3600.
            time_str = '%02d:%02d'%(int(time_hr),float(time_hr)-int(time_hr))
            entry = {'ValidFrom':valid_date,'time':time_str,'Units':bsub[1]}
            out_table_basals.append(entry)

    return out_table_editable, out_table_fixed, out_table_basals

#------------------------------------------------------------------
def tablefToContainers(conts,date) :
    # Up until now we have stored everything in "Tablef" format. NOW we make the containers themselves.

    conts_out = []

    start_time_dt,end_time_dt = Utils.GetDayBeginningAndEnd_dt(date)

    # put all BGs last, for iov_1 calc
    def sort_BG(x) :
        if x['class'] != 'BGMeasurement' :
            return '0'
        return x['iov_0_str']

    conts.sort(key=sort_BG)

    for i in range(len(conts)) :
        c = conts[i]
        iov_0_str = c['iov_0_str']+':00'

        args = []

        # Going to be a bit careful here about ... security?
        the_class = {'BGMeasurement':BGMeasurement,
                     'InsulinBolus':InsulinBolus,
                     'SquareWaveBolus':SquareWaveBolus,
                     'DualWaveBolus':DualWaveBolus,
                     'Food':Food,
                     'TempBasal':TempBasal,
                     'Suspend':Suspend,
                     'LiverFattyGlucose':LiverFattyGlucose,
                     'ExerciseEffect':ExerciseEffect,
                     }.get(c['class'],None)

        if the_class == None :
            continue

        # Get iov_1 in a way that is compatible with the table
        if c['class'] == 'BGMeasurement' :
            try :
                starttime,endtime = iov_0_str,conts[i+1]['iov_0_str']+':00'
            except IndexError :
                starttime,endtime = iov_0_str,end_time_dt.strftime('%Y-%m-%d %H:%M:00')
            try :
                mag = float(c['magnitude'])
            except ValueError :
                continue
            args = starttime,endtime,mag

        elif c['class'] in ['TempBasal','ExerciseEffect'] :
            try :
                iov_1_dt = datetime.datetime.strptime(iov_0_str,'%Y-%m-%d %H:%M:%S')+datetime.timedelta(hours=float(c['duration_hr']))
                iov_1_str = datetime.datetime.strftime(iov_1_dt,'%Y-%m-%d %H:%M:00')
                args = iov_0_str,iov_1_str,float(c['magnitude'])/100.
            except (ValueError, TypeError) as e :
                continue

        # Suspend
        elif c['class'] in ['Suspend'] :
            try :
                iov_1_dt = datetime.datetime.strptime(iov_0_str,'%Y-%m-%d %H:%M:%S')+datetime.timedelta(hours=float(c['duration_hr']))
                iov_1_str = datetime.datetime.strftime(iov_1_dt,'%Y-%m-%d %H:%M:00')
                args = iov_0_str,iov_1_str
            except ValueError :
                continue

        # Square wave
        elif c['class'] == 'SquareWaveBolus' :
            args = iov_0_str,float(c['duration_hr']),float(c['magnitude'])

        # LiverFattyGlucose
        elif c['class'] == 'LiverFattyGlucose' :
            try :
                iov_1_dt = datetime.datetime.strptime(iov_0_str,'%Y-%m-%d %H:%M:%S')+datetime.timedelta(hours=float(c['duration_hr']))
                iov_1_str = datetime.datetime.strftime(iov_1_dt,'%Y-%m-%d %H:%M:00')
                args = iov_0_str,iov_1_str,float(c['magnitude']),max(float(c['duration_hr']),0.1),-999.
            except (ValueError, TypeError) as e :
                continue

        # Dual wave (gross)
        elif c['class'] == 'DualWaveBolus' :
            mag = c['magnitude'].split('/')
            normal = 0
            delayed = 0
            if len(mag) == 1 :
                try :
                    normal = float(mag)
                except ValueError :
                    pass
            elif len(mag) == 2 :
                for m in mag :
                    if 'n' in m :
                        try :
                            normal = float(m.strip('n'))
                        except ValueError :
                            pass
                    if 'd' in m :
                        try :
                            delayed = float(m.strip('n'))
                        except ValueError :
                            pass
            args = iov_0_str,c['duration_hr'],delayed,normal

        # InsulinBolus, Food
        else :
            try :
                args = iov_0_str,float(c['magnitude'])
            except (ValueError, TypeError) as e:
                continue

        # make the container
        try :
            c_out = the_class.FromStringDate(*args)
        except ValueError :
            print('Error: could not make a container from',c.get('class','NoneClass'),'using these args:',args)
            pass

        try :
            c_out.Ta = float(c['duration_hr'])
        except ValueError :
            pass

        conts_out.append(c_out)

    # Add basals
    return conts_out

#------------------------------------------------------------------
def tablefToBasalRates(rows) :

    out_basal = Settings.UserSetting('Basal')

    for row in rows :
        hr = int(row['time'].split(':')[0])
        min = int(row['time'].split(':')[1])
        time_hr = hr+min/60.
        out_basal.AddSettingToSnapshot(row['ValidFrom']+':00',time_hr,row['Units'])

    return out_basal

#------------------------------------------------------------------
def ConvertContainerTablesToActiveList_Tablef(table_ed,table_fix) :
    # In: tableformat, Out: tableformat

    containers = []

    # grab "hidden" containers
    for c in table_fix :
        if 'hidden' in c.keys() :
            for ci in c['hidden'] :
                containers.append(ci)

    if len(table_fix) :
        for c in table_fix :
            containers.append(c)

    if len(table_ed) :
        for c in table_ed :
            containers.append(c)

    return containers

#------------------------------------------------------------------
def UpdateUnits(rows) :
    units = []
    for row in rows :
        if row['class'] == 'Food' :
            units.append({'unit':'g'})
        elif row['class'] in ['TempBasal','ExerciseEffect'] :
            units.append({'unit':'%'})
#         elif row['class'] == 'ExerciseEffect' :
#             units.append({'unit':u'\u26f9'})
#             #units.append({'unit':('\u26f9')*round(float(row['magnitude']))})
        elif row['class'] == 'InsulinBolus' :
            units.append({'unit':'u'})
        elif row['class'] in ['BGMeasurement','LiverFattyGlucose'] :
            units.append({'unit':'mg/dL'})
        else :
            units.append({'unit':''})

        units[-1]['class'] = row['class']

    return units
