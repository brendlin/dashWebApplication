
# A very simple Flask Hello World app for you to get started with...

#from flask import Flask
#app = Flask(__name__)
#@app.route('/')
#def hello_world():
#    return 'Hello from Flask! (Kurt)'

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate
import sys

import datetime

import numpy as np
import pandas as pd
import dash_table
import plotly
import json

# Tools
import ManagePlots
import LoadNewFile
import SettingsTableFunctions
import ContainersTableFunctions
import ManageBGActions
import ManageSettings
import Utils
from ColorSchemes import ColorScheme
import ButtonsAndComponents as comps

# BG Classes
from BGModel import BGActionClasses
from BGModel import Settings

# needed for callbacks
from dash.dependencies import Input, Output, State

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# for deployment, pass app.server (which is the actual flask app) to WSGI etc
app = dash.Dash(external_stylesheets=external_stylesheets)

app.layout = html.Div(
    children=[

        html.H5(children='Modeling blood glucose and the effects of insulin.'),

        #html.Div(children='''The following works with Tidepool and Medtronic 551.'''),

        html.Div(
            [html.Div([comps.upload_data],
                      style={'display':'table-cell','width':'25%'}),
             html.Div(id='uploaded-input-data-status',children=None,style={'display':'table-cell','width':'25%','align':'left'}),
             html.Div([comps.upload_libre],
                      style={'display':'table-cell','width':'25%'}),
             html.Div(id='uploaded-libre-status',children=None,style={'display':'table-cell','width':'25%','align':'left'}),
             ],
            style={'align':'left','width':'100%','display':'table'}
            ),

        # Analysis picker and Events picker Div
        html.Div(
            [html.Div(['''Pick an analysis: ''',
                       comps.analy_mode_dropdown,
                       # use the 'height' below to control the height of this particular row
                       html.Div(style={'display':'inline-block','width':'10px','height':'42px','verticalAlign':'middle'}),
                       html.Div(['''Pick a date: ''',comps.date_picker,],id='date-related-div',style={'display':'none'},),
                       ],
                      className='seven columns',
                      #style={'display': 'inline-block','verticalAlign':'middle'},
                      ),
             html.Div(
                    [html.Div(['''Events: ''',
                               comps.containers_dropdown,
                               html.Div(style={'display':'inline-block','width':'10px','height':'42px','verticalAlign':'middle'}),
                               comps.add_rows,
                               ],
                              style={'display':'table-cell','verticalAlign':'middle'},
                              ),
                     ],
                    style={'padding':'5px','margin-left':'30px','height':'50px','display':'table'},
                    className='five columns',
                    ),
             ],
            className='row',
            ),

        # Graph and Containers Div
        html.Div(
            [html.Div([comps.main_graph,],
                      className='seven columns',),
             html.Div(
                    [comps.allow_insulin,
                     html.P('Food, Fatty events:',style={'margin-bottom':'0px','margin-top':'10px'}),
                     html.Div(ContainersTableFunctions.container_table,style={'display':'table-cell'}),
                     html.Div(ContainersTableFunctions.container_table_units,style={'display':'table-cell'}),
                     html.P('Insulin, BG measurements, Temp basals, etc:',style={'margin-bottom':'0px','margin-top':'10px'}),
                     html.Div(ContainersTableFunctions.container_table_fixed,style={'display':'table-cell'}),
                     html.Div(ContainersTableFunctions.container_table_fixed_units,style={'display':'table-cell'}),
                     html.P('Active basal schedule(s):',style={'margin-bottom':'0px','margin-top':'10px'}),
                     html.Div(ContainersTableFunctions.container_table_basal,style={'display':'table-cell'}),
                     ],
                    className='five columns',
                    style={'height':'400px','maxHeight': '400px', 'overflow': 'scroll','border-style':'solid',
                           'border-width':'thin','border-color':'black','padding':'5px','margin-left':'30px',},
                    ),
             ],
            className='row',
            ),

        # Profiles Div
        html.Div(
            [html.Div(
                    [dcc.Dropdown(id='profiles-dropdown',placeholder='Your profiles',style={'width':'250px','display': 'inline-block','verticalAlign':'middle'},searchable=False),
                     html.Div(style={'width':'20px','display':'inline-block'}),
                     html.Label('Insulin decay time (hr): ',style={'width': '20%','display': 'inline-block','verticalAlign':'middle'}),
                     dcc.Input(id='insulin-decay-time', value='4', type='text',style={'width': '5%','display': 'inline-block','align': 'left','marginRight':'5%','verticalAlign':'middle'}),
                     html.Label('Food decay time (hr): ',style={'width': '20%','display': 'inline-block','verticalAlign':'middle'}),
                     dcc.Input(id='food-decay-time', value='2', type='text',style={'width': '5%','display': 'inline-block','verticalAlign':'middle'}),
                     ],
                    style={'display':'table-cell','verticalAlign':'middle'},
                    ),
             ],
            style={'height':'50px','display':'table','width':'100%'},
            ),

        SettingsTableFunctions.base_settings_table,
        SettingsTableFunctions.derived_settings_table,


        dcc.Markdown(children='''\* Units: "BG" stands for mg/dL.

\*\* The two numbers in each hour column represent "on the hour" (top) and "on the half-hour" (bottom).

\*\*\* "True basal rate" represents what your basal insulin should be, based on your sensitivity and liver glucose settings.
''',
                     style={'display': 'none'},
                     ),

        # here is where all the hidden components get added
        *comps.storage,
        ] # html.Div Children
    ) # html.Div

#
# Upload callback (new)
#
@app.callback([Output('uploaded-input-data-status','children'),
               Output('all-basal-schedules', 'children'),
               Output('profiles-from-data', 'children'),
               Output('bwz-profile','children'),
               Output('upload-container-panda', 'children'),
               Output('upload-smbg-panda','children'),
               Output('upload-basal-panda','children'),
               ],
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def update_file(contents, name):

    return LoadNewFile.LoadNewFile(contents, name)

#
# Change date-picker (based on upload-smbg-panda)
#
@app.callback([Output('my-date-picker-single', 'min_date_allowed'),
               Output('my-date-picker-single', 'max_date_allowed'),
               Output('my-date-picker-single', 'initial_visible_month'),
               Output('my-date-picker-single', 'date'),
               Output('my-date-picker-single', 'disabled'),
               Output('date-related-div', 'style'),
               ],
              [Input('upload-smbg-panda','children'),
               Input('analysis-mode-dropdown','value'),
               ],
              [State('my-date-picker-single', 'min_date_allowed'),
               State('my-date-picker-single', 'max_date_allowed'),
               State('my-date-picker-single', 'initial_visible_month'),
               State('my-date-picker-single', 'date'),
               ]
              )
def update_date_picker(pd_smbg_json,analysis_mode,min_date_old,max_date_old,month_old,date_old):

    if (not pd_smbg_json) or (analysis_mode == 'sandbox') :
        return min_date_old,max_date_old,month_old,date_old,True,{'display':'none'}

    pd_smbg = pd.read_json(pd_smbg_json)

    # dates!
    np_smbg = np.array(pd_smbg['deviceTime'],dtype='datetime64')

    min_date = min(np_smbg)
    max_date = max(np_smbg)
    month    = max_date
    day      = max_date

    disabled = (analysis_mode != 'daily-analysis')
    display_date = {'display':'none'} if disabled else {'display':'inline-block'}

    return min_date,max_date,month,day,disabled,display_date

#
# Upload callback (Libre)
#
@app.callback([Output('uploaded-libre-status','children'),
               Output('upload-cgm-panda', 'children')],
              [Input('upload-libre', 'contents')],
              [State('upload-libre', 'filename')])
def update_file(contents, name):

    return LoadNewFile.LoadLibreFile(contents, name)

#
# Update the plot
#
@app.callback(Output('display-tidepool-graph', 'figure'),
              [Input('upload-smbg-panda', 'children'),
               Input('active-profile', 'children'),
               Input('container-table-editable', 'data'),
               Input('container-table-fixed', 'data'),
               Input('container-table-basal', 'data'),
               Input('analysis-mode-dropdown','value'),
               Input('my-date-picker-single', 'date'),
               ],
              [State('upload-cgm-panda','children'),
               State('upload-basal-panda','children'),
               ])
def update_plot(pd_smbg_json,active_profile_json,table_ed,table_fix,table_basal,analysis_mode,date,pd_cgm_json,pd_basal_json):

    if (not pd_smbg_json) :
        # Don't worry - this will be updated by default from the Upload callback
        raise PreventUpdate

    if (analysis_mode == 'data-overview') :
       return ManagePlots.doOverview(pd_smbg_json,pd_cgm_json)

    if analysis_mode in ['daily-analysis','sandbox'] :
        if not table_basal :
            raise PreventUpdate

    if (analysis_mode == 'daily-analysis') :
        return ManagePlots.doDayPlot(pd_smbg_json,active_profile_json,table_ed,table_fix,table_basal,date,pd_cgm_json,pd_basal_json)

    if (analysis_mode == 'sandbox') :
        return ManagePlots.doDayPlot(pd_smbg_json,active_profile_json,table_ed,table_fix,table_basal,date,pd_cgm_json,pd_basal_json,isSandbox=True)

    if (analysis_mode == 'cgm-plot') :
        return ManagePlots.doCGMAnalysis(pd_smbg_json,pd_cgm_json)

    return {}

#
# Update the dropdown of available containers (when a day is selected)
#
@app.callback([Output('containers-dropdown', 'options'),
               Output('containers-dropdown', 'value'),
               Output('bwz-containers', 'children'),
               ],
              [Input('analysis-mode-dropdown','value'),
               Input('my-date-picker-single', 'date'),
               ],
              [
               State('upload-smbg-panda', 'children'),
               State('all-basal-schedules','children'),
               State('upload-container-panda','children'),
               State('upload-basal-panda','children'),
               State('bwz-profile', 'children'), # make the containers (fatty) from the original bwz
               State('containers-dropdown', 'options'),
               State('containers-dropdown', 'value'),
               ])
def make_day_containers(analysis_mode,date,pd_smbg_json,basals_json,pd_cont_json,pd_basal_json,bwz_profile_json,options,value):

    loadDayContainers = analysis_mode in ['daily-analysis','sandbox']

    if not loadDayContainers :
        return [], None, ''

    if not pd_smbg_json or not pd_cont_json or not bwz_profile_json or not pd_basal_json :
        return [], None, ''

    pd_smbg = pd.read_json(pd_smbg_json)
    pd_cont = pd.read_json(pd_cont_json)
    active_profile = Settings.TrueUserProfile.fromJson(bwz_profile_json.split('$$$')[1])
    pd_basal = pd.read_json(pd_basal_json)

    tmp_date = Utils.sandbox_date if (analysis_mode == 'sandbox') else date
    start_time_dt,end_time_dt = Utils.GetDayBeginningAndEnd_dt(tmp_date)

    # Get all the basal settings for this particular day
    basals = Settings.UserSetting.fromJson(basals_json)
    basals = ManageSettings.GetProgrammedBasalsInRange(basals,start_time_dt,end_time_dt)

    bwz_conts_Tablef = ManageBGActions.GetContainers_Tablef(pd_smbg,pd_cont,basals,active_profile,start_time_dt,end_time_dt,pd_basal)

    # sandbox mode: Add a BG measurement at the beginning so that the plot populates.
    if analysis_mode == 'sandbox' and len(bwz_conts_Tablef) == 2 :
        bwz_conts_Tablef.append({'class':'BGMeasurement','magnitude':115,'hr':'hr','duration_hr':'-',
                                 'iov_0_str':ManageBGActions.FormatTimeString(Utils.sandbox_date)})

    the_time = start_time_dt.strftime('%Y-%m-%d')
    the_name = '%s BWZ Inputs'%(the_time)
    the_name_time_tagged = '@%s BWZ Inputs'%(the_time)
    bwz_conts_json = Utils.WrapUpDayContainers(the_name_time_tagged,bwz_conts_Tablef,basals)

    if the_name not in list(o['label'] for o in options) :
        options.append({'label':the_name,'value':bwz_conts_json})

    if not value or ('@%s'%the_time) not in value :
        value = bwz_conts_json

    for opt in options :
        opt['disabled'] = (('@%s'%the_time) not in opt['value'])

    return options, value, bwz_conts_json

#
# Update the list of available profiles
#
@app.callback([Output('profiles-dropdown', 'options'),
               Output('profiles-dropdown', 'value')],
              [Input('profiles-from-data', 'children'),
               Input('custom-profiles', 'children'),
               Input('analysis-mode-dropdown', 'value'),
               ],
              [State('last-profile-selected','children'),
               ])
def update_dropdown(profiles_from_data_json,custom_profiles_json,analysis_mode,previous_value) :

    if not profiles_from_data_json :
        raise PreventUpdate

    value_generic_userprofile = ''
    options = []

    for each_profile in profiles_from_data_json.split('###') :
        key,value = each_profile.split('$$$')
        the_datetime = datetime.datetime.strptime(key,'%Y-%m-%dT%H:%M:%S')
        key_short = 'profile from %s'%(the_datetime.strftime('%Y-%m-%d'))

        # just a little bit of disambiguation in case values are identical:
        value = value.replace('}',',"key":"%s"}'%(key))

        if '1970' in key :
            key_short = 'A generic user profile'
            value_generic_userprofile = value

        # If there were multiple changes within one hour, pick only one.
        doSkip = False
        for index in range(len(options)) :
            time_diff = (the_datetime - options[index]['datetime']).total_seconds()
            # if >24 hour separation, keep both
            if abs(time_diff) > 60*60*24 :
                continue
            # keep the newer one, if within 1 hour
            if 0 < time_diff and time_diff < 60*60 :
                options.pop(index)
            elif 0 > time_diff and time_diff > -60*60 :
                doSkip = True
            # if < 24 and > 1 hour separation, keep both and relabel
            else :
                key_short = 'profile from %s'%(the_datetime.strftime('%Y-%m-%d %H:%M'))
                options[index]['label'] = 'profile from %s'%(options[index]['datetime'].strftime('%Y-%m-%d %H:%M'))

        if doSkip :
            continue

        options.append({'label':key_short,'value':value,'datetime':the_datetime})

    for i in range(len(options)) :
        options[i].pop('datetime')

    if analysis_mode == 'sandbox' :
        # return options, value to display, last-status value
        return options, value_generic_userprofile

    new_value = previous_value
    if not new_value :
        new_value = options[-1]['value']

    # return options, value to display, last-status (non-sandbox) value
    return options, new_value

#
# Update the last profile selected
#
@app.callback([Output('last-profile-selected', 'children'),
               ],
              [Input('profiles-dropdown', 'value'),
               Input('analysis-mode-dropdown', 'value'),
               ])
def update_dropdown(current_value,analysis_mode) :

    if not current_value :
        raise PreventUpdate

    if analysis_mode == 'sandbox' :
        raise PreventUpdate

    return [current_value]

#
# Update the base table
#
@app.callback(Output('base_settings_table', 'data'),
              [Input('profiles-dropdown', 'value')])
def update_base_settings(new_profile_selected_from_dropdown):

    return SettingsTableFunctions.UpdateBaseTable(new_profile_selected_from_dropdown)

#
# Update InsulinTa
#
@app.callback(Output('insulin-decay-time', 'value'),
              [Input('profiles-dropdown', 'value')])
def update_insulin_ta_inpudata(new_profile_selected_from_dropdown):

    if not new_profile_selected_from_dropdown :
        return 4

    return Settings.TrueUserProfile.fromJson(new_profile_selected_from_dropdown).getInsulinTaHrMidnight(0)

#
# Update FoodTa
#
@app.callback(Output('food-decay-time', 'value'),
              [Input('profiles-dropdown', 'value')])
def update_insulin_ta_inpudata(new_profile_selected_from_dropdown):

    if not new_profile_selected_from_dropdown :
        return 2

    return Settings.TrueUserProfile.fromJson(new_profile_selected_from_dropdown).getFoodTaHrMidnight(0)

#
# Update derived table
#
@app.callback(Output('derived_settings_table', 'data'),
              [Input('base_settings_table', 'data'),
               Input('insulin-decay-time', 'value')])
def update_derived_table(table,ta):

    if not ta :
        raise PreventUpdate

    try :
        float(ta)
    except ValueError :
        raise PreventUpdate

    return SettingsTableFunctions.UpdateDerivedTable(table,ta)


#
# Update the active settings from the table
#
@app.callback(Output('active-profile', 'children'),
              [Input('base_settings_table', 'data'),
               Input('insulin-decay-time', 'value'),
               Input('food-decay-time', 'value')])
def update_active_profile(table,ta,tf):

    if (not ta) or (not tf) :
        raise PreventUpdate

    try :
        float(ta) and float(tf)
    except ValueError :
        raise PreventUpdate

    return SettingsTableFunctions.ConvertBaseTableToProfile(table,ta,tf)

#
# Populate container tables (or add new rows)
#
@app.callback([Output('container-table-editable', 'data'),
               Output('container-table-fixed', 'data'),
               Output('container-table-basal', 'data'),
               ],
              [Input('add-rows-button', 'n_clicks'),
               Input('containers-dropdown','value'),
               ],
              [State('container-table-editable', 'data'),
               State('container-table-editable', 'columns'),
               State('container-table-fixed', 'data'),
               State('container-table-fixed', 'columns'),
               State('container-table-basal', 'data'),
               State('container-table-basal', 'columns'),
               State('my-date-picker-single', 'date'),
               State('analysis-mode-dropdown', 'value'),
               ])
def make_container_tables(n_clicks, containers_selected_from_dropdown,
                          rows_ed, columns_ed, rows_fix, columns_fix, rows_basal, columns_basal,
                          date, analysis_mode):

    if not dash.callback_context.triggered:
        raise PreventUpdate

    tmp_date = Utils.sandbox_date if (analysis_mode == 'sandbox') else date

    # If the user requested a new row:
    if (n_clicks > 0) and ('n_clicks' in dash.callback_context.triggered[0]['prop_id']) :
        next = {c['id']: '' for c in columns_fix}
        next['class'] = 'Add an event'
        next['IsBWZ'] = 0
        if 'YYYY' in rows_ed[-1]['iov_0_str'] :
            next['iov_0_str'] = rows_ed[-1]['iov_0_str']
        elif analysis_mode == 'sandbox' :
            next['iov_0_str'] = Utils.sandbox_date.split(' ')[0].split('T')[0]+' 04:00'
        else :
            next['iov_0_str'] = date.split(' ')[0].split('T')[0]+' 04:00'
        next['hr'] = 'hr'
        rows_ed.append(next)
        return rows_ed, rows_fix, rows_basal

    # Otherwise, it was a new dropdown:
    return ContainersTableFunctions.UpdateContainerTable(containers_selected_from_dropdown,tmp_date)

#
# Update units table to reflect container table
#
@app.callback(Output('container-table-editable-units', 'data'),
              [Input('container-table-editable','data')],
              )
def update_units_editable(rows) :
    return ContainersTableFunctions.UpdateUnits(rows)

@app.callback(Output('container-table-fixed-units', 'data'),
              [Input('container-table-fixed','data')],
              )
def update_units_fixed(rows) :
    return ContainersTableFunctions.UpdateUnits(rows)

#
# Allow "fixed" containers to be edited
#
@app.callback([Output('container-table-fixed', 'editable'),
               Output('container-table-editable','dropdown_conditional'),
               ],
              [Input('allow-insulin','value')],
              )
def allow_insulin_edits(allow_bool) :

    container_opts = []
    for opt in ContainersTableFunctions.container_opts :
        container_opts.append(opt)

    if allow_bool :
        container_opts += ['InsulinBolus','TempBasal','BGMeasurement']

    conditional = [{'if': {'column_id': 'class',
                           'filter_query': '{IsBWZ} eq "0"'},
                    'options': list({'label': i, 'value': i} for i in container_opts),
                    'clearable':False,
                    },
                   ]

    return bool(allow_bool), conditional

app.title = 'Kurt Webpage'

# This is apparently okay to deploy too.
if __name__ == '__main__':
    app.run_server(debug=True)
