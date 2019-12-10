
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

# Tools
import ManagePlots
import LoadNewFile
import SettingsTableFunctions
import SettingsSliders

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

        html.H5(children='Modeling blood glucose and the effects of insulin'),

        html.Div(children='''The following works with Tidepool and Medtronic 551.'''),

        html.Div([html.Div(dcc.Upload(id='upload-data',
                                      children=[html.Button('Upload your own data from Tidepool',style={'width':'400px','display':'table-cell'})],
                                      multiple=False,
                                      style={'width':'400px','display':'table-cell'}
                                      ),
                           style={'display':'table-cell','width':'450px'}),
                  html.Div(id='uploaded-input-data-status',children=None,style={'display':'table-cell','width':'50%'})
                  ],
                 style={'align':'left','width':'100%','display':'table'}
                 ),

        # Saved profiles (panda)
        html.Div(id='active-profile'    ,style={'display': 'none'},children=None), # This will store the json text
        html.Div(id='profiles-from-data',style={'display': 'none'},children=None), # This will store the json text
        html.Div(id='custom-profiles'   ,style={'display': 'none'},children=None), # This will store the json text

        # Saved basal schedules (panda)
        html.Div(id='all-basal-schedules',style={'display':'none'},children='blahblah'), # This stores the historical basal schedules

        # Sub-panda datasets from raw file
        html.Div(id='upload-smbg-panda'     ,style={'display': 'none'},children=None), # This stores the historical basal schedules
        html.Div(id='upload-container-panda',style={'display': 'none'},children=None), # This stores the historical basal schedules
        html.Div(id='upload-settings-panda' ,style={'display': 'none'},children=None), # This stores the historical basal schedules

        html.Div(children=['''Pick a date:''',
                           dcc.DatePickerSingle(id='my-date-picker-single',
                                                min_date_allowed=datetime.datetime(1995, 8, 5),
                                                max_date_allowed=datetime.datetime(2017, 9, 19),
                                                initial_visible_month=datetime.datetime(2017, 8, 5),
                                                date=str(datetime.datetime(2017, 8, 25, 23, 59, 59))
                                                ),
                           html.Button('Show this day', id='show-this-day'),
                           html.Button('Back to overview', id='overview-button'),
                           ]
                 ),


        html.Div(children = [
                html.Hr(),  # horizontal line
                dcc.Graph(id='display-tidepool-graph',
                          #config={'staticPlot':True,},
                          figure={}
                          ), # Graph
                html.Hr(),  # horizontal line
                ]
                 ),

        html.Div(html.Div([dcc.Dropdown(id='profiles-dropdown',placeholder='Your profiles',style={'width':'250px','display': 'inline-block','verticalAlign':'middle'}),
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

        html.Hr(),  # horizontal line

        *SettingsSliders.slider_divs,

        html.Hr(),  # horizontal line

        SettingsTableFunctions.base_settings_table,
        SettingsTableFunctions.derived_settings_table,

        dcc.Markdown(children='''\* Units: "BG" stands for mg/dL.

\*\* The two numbers in each hour column represent "on the hour" (top) and "on the half-hour" (bottom).

\*\*\* "True basal rate" represents what your basal insulin should be, based on your sensitivity and liver glucose settings.
'''
                      ),

        ] # html.Div Children
    ) # html.Div

#
# Upload callback (new)
#
@app.callback([Output('uploaded-input-data-status','children'),
               Output('all-basal-schedules', 'children'),
               Output('profiles-from-data', 'children'),
               Output('my-date-picker-single', 'min_date_allowed'),
               Output('my-date-picker-single', 'max_date_allowed'),
               Output('my-date-picker-single', 'initial_visible_month'),
               Output('my-date-picker-single', 'date'),
               Output('upload-container-panda', 'children'),
               Output('upload-smbg-panda','children'),
               ],
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def update_file(contents, name):

    return LoadNewFile.LoadNewFile(contents, name)

#
# Update the plot
#
@app.callback(Output('display-tidepool-graph', 'figure'),
              [Input('upload-smbg-panda', 'children'),
               Input('active-profile', 'children'),
               Input('show-this-day','n_clicks_timestamp'),
               Input('overview-button','n_clicks_timestamp')],
              [State('my-date-picker-single', 'date'),
               State('all-basal-schedules','children'),
               State('upload-container-panda','children'),])
def update_plot(pd_smbg_json,active_profile_json,show_this_day_t,show_overview_t,date,basals_json,pd_cont_json):

    #print('basals_json',basals_json)
    #print('active_profile_json',active_profile_json)
    #print('pd_cont_json',('Exists.' if pd_cont_json else 'Empty.'))

    if (not pd_smbg_json) :
        # Don't worry - this will be updated by default from the Upload callback
        return {}

    pd_smbg = pd.read_json(pd_smbg_json)

    thisDayWasPressed = (show_this_day_t != None)
    overviewNeverPressed = (show_overview_t == None)
    doDayPlot = thisDayWasPressed and (overviewNeverPressed or (show_this_day_t > show_overview_t))

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
        try :
            the_time = datetime.datetime.strptime(date,'%Y-%m-%dT%H:%M:%S')
        except ValueError :
            the_time = datetime.datetime.strptime(date,'%Y-%m-%d')
        start_time = the_time.strftime('%Y-%m-%dT04:00:00')
        end_time  = (the_time+datetime.timedelta(days=1)).strftime('%Y-%m-%dT10:00:00')

    else :
        start_time = pd_smbg['deviceTime'].iloc[-1]
        end_time   = pd_smbg['deviceTime'].iloc[0]

    start_time_dt = datetime.datetime.strptime(start_time,'%Y-%m-%dT%H:%M:%S')
    end_time_dt   = datetime.datetime.strptime(end_time  ,'%Y-%m-%dT%H:%M:%S')

    fig.update_yaxes(title_text="BG (mg/dL)", row=1, col=1)
    fig.update_yaxes(title_text=u"\u0394"+" BG (mg/dL/hr)", row=2, col=1)
    fig.update_xaxes(range=[start_time_dt, end_time_dt])
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20),paper_bgcolor="LightSteelBlue",)

    smbg_plot = ManagePlots.GetPlotSMBG(pd_smbg,start_time_dt,end_time_dt)
    fig.append_trace(smbg_plot,1,1)

    if not doDayPlot :
        return fig

    #fig.update_layout(transition={'duration': 500})

    # After this point, we assume we are doing the full analysis.
    pd_cont = pd.read_json(pd_cont_json)
    basals = Settings.UserSetting.fromJson(basals_json)
    active_profile = Settings.TrueUserProfile.fromJson(active_profile_json)

    plots = ManagePlots.GetAnalysisPlots(pd_smbg,pd_cont,basals,active_profile,start_time_dt,end_time_dt)
    for plot in plots[0] :
        fig.append_trace(plot,1,1)
    for plot in plots[1] :
        fig.append_trace(plot,2,1)

    return fig

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

    return SettingsTableFunctions.ConvertBaseTableToProfile(table,ta,tf)

#
# Update slider echos
#
# @app.callback(Output('slider-echos-master-%s'%('sensitivity'), 'children'),
#               list(Input('slider-%s-%d'%('sensitivity',i),'value') for i in range(24)))
# def update_echo_master(*args) :
#     return SettingsSliders.UpdateListOfEchos('sensitivity',*args)

# @app.callback(Output('slider-echos-master-%s'%('food'), 'children'),
#               list(Input('slider-%s-%d'%('food',i),'value') for i in range(24)))
# def update_echo_master(*args) :
#     return SettingsSliders.UpdateListOfEchos('food',*args)

# @app.callback(Output('slider-echos-master-%s'%('liver'), 'children'),
#               list(Input('slider-%s-%d'%('liver',i),'value') for i in range(24)))
# def update_echo_master(*args) :
#     return SettingsSliders.UpdateListOfEchos('liver',*args)

#
# Update sliders
#
# @app.callback(Output('slider-sensitivity-0', 'value'),
#               [Input('uploaded-input-data-flag', 'children')])
# def update_a_slider_sensitivity_0(value):
#     return SettingsSliders.UpdateSlider('sensitivity',0,my_globals)

#
# Update sliders - dynamically generated functions (a little slow...)
#
# def make_update_slider(setting,i) :

#     def callback(value) :
#         return SettingsSliders.UpdateSlider(setting,i,my_globals)

#     return callback

# for setting in ['sensitivity','food','liver'] :
#     for i in range(24) :
#         dynamically_generated_slider_update = make_update_slider(setting,i)
#         app.callback(Output('slider-%s-%d'%(setting,i), 'value'),
#                      [Input('uploaded-input-data-flag', 'children')])(dynamically_generated_slider_update)

@app.callback(list(Output('slider-%s-%d'%(setting,i),'value') for setting in ['sensitivity','food','liver'] for i in range(24)),
              [Input('uploaded-input-data-flag', 'children')])
def update_sliders_from_newdata(update_indicator) :
    outputs = []
    for setting in ['sensitivity','food','liver'] :
        for i in range(24) :
            outputs.append(SettingsSliders.UpdateSlider(setting,i,my_globals))
    print(outputs)
    return outputs

app.title = 'Kurt Webpage'

# This is apparently okay to deploy too.
if __name__ == '__main__':
    app.run_server(debug=True)
