
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
import Utils

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

        html.Div([html.Div(dcc.Upload(id='upload-data',
                                      children=[html.Button('Upload from Tidepool',style={'width':'95%','display':'table-cell'})],
                                      multiple=False,
                                      style={'width':'300px','display':'table-cell'}
                                      ),
                           style={'display':'table-cell','width':'25%'}),
                  html.Div(id='uploaded-input-data-status',children=None,style={'display':'table-cell','width':'25%','align':'left'}),
                  html.Div(dcc.Upload(id='upload-libre',
                                      children=[html.Button('Upload from Libre',style={'width':'95%','display':'table-cell'})],
                                      multiple=False,
                                      style={'width':'25%','display':'table-cell'}
                                      ),
                           style={'display':'table-cell','width':'25%'}),
                  html.Div(id='uploaded-libre-status',children=None,style={'display':'table-cell','width':'25%','align':'left'}),
                  ],
                 style={'align':'left','width':'100%','display':'table'}
                 ),

        # Saved profiles (panda)
        html.Div(id='active-profile'    ,style={'display': 'none'},children=None), # This will store the json text
        html.Div(id='profiles-from-data',style={'display': 'none'},children=None), # This will store the json text
        html.Div(id='custom-profiles'   ,style={'display': 'none'},children=None), # This will store the json text
        html.Div(id='bwz-profile'       ,style={'display': 'none'},children=None), # This will store the json text

        # Saved container profiles
        html.Div(id='active-containers'      ,style={'display': 'none'},children=None),
        html.Div(id='bwz-containers',style={'display': 'none'},children=None),
        html.Div(id='custom-containers'      ,style={'display': 'none'},children=None),

        # Saved basal schedules (panda)
        html.Div(id='all-basal-schedules',style={'display':'none'},children=None), # This stores the historical basal schedules

        # Sub-panda datasets from raw file
        html.Div(id='upload-smbg-panda'     ,style={'display': 'none'},children=None), # This stores the historical basal schedules
        html.Div(id='upload-container-panda',style={'display': 'none'},children=None), # This stores the historical basal schedules
        html.Div(id='upload-settings-panda' ,style={'display': 'none'},children=None), # This stores the historical basal schedules
        html.Div(id='upload-cgm-panda'      ,style={'display': 'none'},children=None), # This stores the historical basal schedules
        html.Div(id='upload-basal-panda'    ,style={'display': 'none'},children=None),

        html.Div(children=['''Pick a date: ''',
                           dcc.DatePickerSingle(id='my-date-picker-single',
                                                min_date_allowed=datetime.datetime(1995, 8, 5),
                                                max_date_allowed=datetime.datetime(2017, 9, 19),
                                                initial_visible_month=datetime.datetime(2017, 8, 5),
                                                date=str(datetime.datetime(2017, 8, 25, 23, 59, 59))
                                                ),
                           html.Button('Show this day', id='show-this-day',className='button-primary'),
                           html.Button('Back to overview', id='overview-button'),
                           ]
                 ),


        html.Div([html.Div([dcc.Graph(id='display-tidepool-graph',
                                      #config={'staticPlot':True,},
                                      figure={'layout':{'margin':{'l':60, 'r':20, 't':20, 'b':20},
                                                        'paper_bgcolor':'LightSteelBlue',
                                                        'yaxis':{'title':'BG (mg/dL)','range':[30,500]}}},
                                      style={'height': 400,}
                                      ),
                            ],
                           className='seven columns',
                           ),
                  html.Div([html.Div(html.Div([dcc.Dropdown(id='containers-dropdown',placeholder='Daily events',style={'width':'250px','display': 'inline-block','verticalAlign':'middle'},searchable=False),],
                                              style={'display':'table-cell','verticalAlign':'middle'},
                                              ),
                                     style={'height':'50px','display':'table','width':'100%'},
                                     ),
                            html.Div(ContainersTableFunctions.container_table,style={'display':'table-cell'}),
                            html.Div(ContainersTableFunctions.container_table_units,style={'display':'table-cell'}),
                            html.Button('Add row', id='add-rows-button', n_clicks=0,style={'display':'table-cell'}),
                            dcc.Checklist(id='allow-insulin',
                                          options=[{'label':'Allow user-input insulin, BG measurement, temp basal, etc.','value':'allow-insulin'}],
                                          value=[]),
                            html.Div(ContainersTableFunctions.container_table_fixed,style={'display':'table-cell'}),
                            html.Div(ContainersTableFunctions.container_table_fixed_units,style={'display':'table-cell'}),
                            ],
                           className='five columns',
                           style={'height':'400px','maxHeight': '400px', 'overflow': 'scroll'},
                           ),
                  ],
                 className='row',
                 ),

        html.Div(html.Div([dcc.Dropdown(id='profiles-dropdown',placeholder='Your profiles',style={'width':'250px','display': 'inline-block','verticalAlign':'middle'},searchable=False),
                           html.Div(style={'width':'20px','display':'inline-block'}),
                           html.Label('Insulin decay time (hr): ',style={'width': '20%','display': 'inline-block','verticalAlign':'middle'}),
                           dcc.Input(id='insulin-decay-time', value='4', type='text',style={'width': '5%','display': 'inline-block','align': 'left','marginRight':'5%','verticalAlign':'middle'}),
                           html.Label('Food decay time (hr): ',style={'width': '20%','display': 'inline-block','verticalAlign':'middle'}),
                           dcc.Input(id='food-decay-time', value='2', type='text',style={'width': '5%','display': 'inline-block','verticalAlign':'middle'}),
                           ],
                          style={'display':'table-cell','verticalAlign':'middle'},
                          ),
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

        ] # html.Div Children
    ) # html.Div

#
# Upload callback (new)
#
@app.callback([Output('uploaded-input-data-status','children'),
               Output('all-basal-schedules', 'children'),
               Output('profiles-from-data', 'children'),
               Output('bwz-profile','children'),
               Output('my-date-picker-single', 'min_date_allowed'),
               Output('my-date-picker-single', 'max_date_allowed'),
               Output('my-date-picker-single', 'initial_visible_month'),
               Output('my-date-picker-single', 'date'),
               Output('upload-container-panda', 'children'),
               Output('upload-smbg-panda','children'),
               Output('upload-basal-panda','children'),
               ],
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def update_file(contents, name):

    return LoadNewFile.LoadNewFile(contents, name)

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
               Input('active-containers','children'),
               Input('show-this-day','n_clicks_timestamp'),
               Input('overview-button','n_clicks_timestamp')],
              [State('my-date-picker-single', 'date'),
               State('all-basal-schedules','children'),
               State('upload-container-panda','children'),
               State('upload-cgm-panda','children'),
               State('upload-basal-panda','children'),
               ])
def update_plot(pd_smbg_json,active_profile_json,active_containers_json,show_this_day_t,show_overview_t,date,basals_json,pd_cont_json,pd_cgm_json,pd_basal_json):

    #print('basals_json',basals_json)
    #print('active_profile_json',active_profile_json)
    #print('pd_cont_json',('Exists.' if pd_cont_json else 'Empty.'))

    if (not pd_smbg_json) :
        # Don't worry - this will be updated by default from the Upload callback
        return {}

    pd_smbg = pd.read_json(pd_smbg_json)

    doDayPlot = Utils.ShowDayNotOverview(show_this_day_t,show_overview_t)

    # some more sanity guards:
    if (not pd_cont_json) :
        doDayPlot = False

    doOverview = not doDayPlot

    if doOverview :
        fig = plotly.subplots.make_subplots(rows=1,cols=1,shared_xaxes=True)
    if doDayPlot :
        fig = plotly.subplots.make_subplots(rows=2, cols=1,shared_xaxes=True,vertical_spacing=0.02)

    # Get the right timing
    if doDayPlot :
        start_time_dt,end_time_dt = Utils.GetDayBeginningAndEnd_dt(date)

    else :
        start_time = pd_smbg['deviceTime'].iloc[-1]
        end_time   = pd_smbg['deviceTime'].iloc[0]

        start_time_dt = datetime.datetime.strptime(start_time,'%Y-%m-%dT%H:%M:%S')
        end_time_dt   = datetime.datetime.strptime(end_time  ,'%Y-%m-%dT%H:%M:%S')

    fig.update_yaxes(title_text="BG (mg/dL)", row=1, col=1)
    fig.update_yaxes(title_text=u"\u0394"+" BG (mg/dL/hr)", row=2, col=1)
    fig.update_yaxes(range=[30,500], row=1, col=1)
    fig.update_xaxes(range=[start_time_dt, end_time_dt])
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20),paper_bgcolor="LightSteelBlue",)
    fig.update_layout(showlegend=False)

    # Add the cgm
    if pd_cgm_json and doDayPlot :
        pd_cgm = pd.read_json(pd_cgm_json)

        cgm_plot = ManagePlots.GetPlotCGM(pd_cgm,start_time_dt,end_time_dt)
        fig.append_trace(cgm_plot,1,1)

    # Add the smbg plot
    smbg_plot = ManagePlots.GetPlotSMBG(pd_smbg,start_time_dt,end_time_dt)
    fig.append_trace(smbg_plot,1,1)

    if not doDayPlot :
        return fig

    fig.update_yaxes(range=[30,350], row=1, col=1)
    #fig.update_layout(transition={'duration': 500})

    # After this point, we assume we are doing the full analysis.
    pd_cont = pd.read_json(pd_cont_json)
    basals = Settings.UserSetting.fromJson(basals_json)
    active_profile = Settings.TrueUserProfile.fromJson(active_profile_json)
    pd_basal = pd.read_json(pd_basal_json)

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

    plots = ManagePlots.GetAnalysisPlots(pd_smbg,pd_cont,basals,active_containers,active_profile,start_time_dt,end_time_dt,pd_basal)
    for plot in plots[0] :
        fig.append_trace(plot,1,1)
    for plot in plots[1] :
        fig.append_trace(plot,2,1)

    return fig

#
# Update the dropdown of available containers (when a day is selected)
#
@app.callback([Output('containers-dropdown', 'options'),
               Output('containers-dropdown', 'value'),
               Output('bwz-containers', 'children'),
               ],
              [Input('show-this-day','n_clicks_timestamp'),
               Input('overview-button','n_clicks_timestamp')],
              [State('my-date-picker-single', 'date'),
               State('upload-smbg-panda', 'children'),
               State('all-basal-schedules','children'),
               State('upload-container-panda','children'),
               State('upload-basal-panda','children'),
               State('bwz-profile', 'children'), # make the containers (fatty) from the original bwz
               State('containers-dropdown', 'options'),
               State('containers-dropdown', 'value'),
               ])
def make_day_containers(show_this_day_t,show_overview_t,date,pd_smbg_json,basals_json,pd_cont_json,pd_basal_json,bwz_profile_json,options,value):

    loadDayContainers = Utils.ShowDayNotOverview(show_this_day_t,show_overview_t)

    if not loadDayContainers :
        return [], None, ''

    pd_smbg = pd.read_json(pd_smbg_json)
    pd_cont = pd.read_json(pd_cont_json)
    basals = Settings.UserSetting.fromJson(basals_json)
    active_profile = Settings.TrueUserProfile.fromJson(bwz_profile_json.split('$$$')[1])
    pd_basal = pd.read_json(pd_basal_json)

    start_time_dt,end_time_dt = Utils.GetDayBeginningAndEnd_dt(date)

    bwz_conts_Tablef = ManageBGActions.GetContainers_Tablef(pd_smbg,pd_cont,basals,active_profile,start_time_dt,end_time_dt,pd_basal)

    the_time = start_time_dt.strftime('%Y-%m-%d')
    the_name = '%s BWZ Inputs'%(the_time)
    the_name_time_tagged = '@%s BWZ Inputs'%(the_time)
    bwz_conts_json = '$$$'.join([the_name_time_tagged]+list(json.dumps(c) for c in bwz_conts_Tablef))

    if the_name not in list(o['label'] for o in options) :
        options.append({'label':the_name,'value':bwz_conts_json})

    if not value or ('@%s'%the_time) not in value :
        value = bwz_conts_json

    for opt in options :
        opt['disabled'] = (('@%s'%the_time) not in opt['value'])

    return options, value, bwz_conts_json

#
# Update the list of available menus
#
@app.callback([Output('profiles-dropdown', 'options'),
               Output('profiles-dropdown', 'value')],
              [Input('profiles-from-data', 'children'),
               Input('custom-profiles', 'children')],
              [State('profiles-dropdown','value')])
def update_dropdown(profiles_from_data_json,custom_profiles_json,previous_value) :

    options = []
    new_value = previous_value

    if profiles_from_data_json :
        profiles = dict()
        for each_profile in profiles_from_data_json.split('###') :
            key,value = each_profile.split('$$$')
            key_short = 'profile from %s'%(datetime.datetime.strptime(key,'%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d'))
            if '1970' in key :
                key_short = 'A generic user profile'
            options.append({'label':key_short,'value':value})

        if not new_value :
            new_value = options[-1]['value']

    return options, new_value

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
# Update the active containers from the table
#
@app.callback(Output('active-containers', 'children'),
              [Input('container-table-editable', 'data'),
               Input('container-table-fixed', 'data'),
               ],
              )
def convert_container_tables_to_active(table_ed,table_fix) :

    return ContainersTableFunctions.ConvertContainerTablesToActiveList_Tablef(table_ed,table_fix)

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
               ],
              [Input('add-rows-button', 'n_clicks'),
               Input('containers-dropdown','value'),
               ],
              [State('container-table-editable', 'data'),
               State('container-table-editable', 'columns'),
               State('container-table-fixed', 'data'),
               State('container-table-fixed', 'columns'),
               State('my-date-picker-single', 'date'),
               ])
def make_container_tables(n_clicks, containers_selected_from_dropdown, rows_ed, columns_ed, rows_fix, columns_fix, date):

    if not dash.callback_context.triggered:
        raise PreventUpdate

    # If the user requested a new row:
    if (n_clicks > 0) and ('n_clicks' in dash.callback_context.triggered[0]['prop_id']) :
        next = {c['id']: '' for c in columns_fix}
        next['class'] = 'Add an event'
        next['IsBWZ'] = 0
        if 'YYYY' in rows_ed[-1]['iov_0_str'] :
            next['iov_0_str'] = rows_ed[-1]['iov_0_str']
        else :
            next['iov_0_str'] = date.split(' ')[0].split('T')[0]+' 00:00'
        next['hr'] = 'hr'
        rows_ed.append(next)
        return rows_ed, rows_fix

    # Otherwise, it was a new dropdown:
    return ContainersTableFunctions.UpdateContainerTable(containers_selected_from_dropdown,date)

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
