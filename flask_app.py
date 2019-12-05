
# A very simple Flask Hello World app for you to get started with...

#from flask import Flask
#app = Flask(__name__)
#@app.route('/')
#def hello_world():
#    return 'Hello from Flask! (Kurt)'

import dash
import dash_core_components as dcc
import dash_html_components as html
import sys

import datetime

import numpy as np
import dash_table

# Tools
import ManageSettings
import ManagePlots
import LoadNewFile
import SettingsTableFunctions

# BG Classes
from BGModel import BGActionClasses

# needed for callbacks
from dash.dependencies import Input, Output, State

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# Make some globals that we can overwrite, refer to, etc.
my_globals = dict()
my_globals['global_df'] = 0
my_globals['pd_smbg'] = 0
my_globals['pd_settings'] = 0
my_globals['bwz_settings'] = []
my_globals['current_setting'] = 0
my_globals['basal_schedules'] = 0
my_globals['containers'] = dict()

# for deployment, pass app.server (which is the actual flask app) to WSGI etc
app = dash.Dash(external_stylesheets=external_stylesheets)

app.layout = html.Div(
    children=[

        html.H1(children='Modeling blood glucose and the effects of insulin'),

        html.Div(children='''The following works with Tidepool and Medtronic 551.'''),

        dcc.Upload(id='upload-data',
                   children=[html.Button('Upload your own data from Tidepool')],
                   multiple=False,
                   ),

        html.Div(id='uploaded-input-data-flag',children=None),

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

        html.Label('Insulin decay time (hr): ',style={'width': '15%','display': 'inline-block'}),
        dcc.Input(id='insulin-decay-time', value='4', type='text',style={'width': '5%','display': 'inline-block','align': 'left','marginRight':'5%'}),
        html.Label('Food decay time (hr): ',style={'width': '15%','display': 'inline-block'}),
        dcc.Input(id='food-decay-time', value='2', type='text',style={'width': '5%','display': 'inline-block'}),

        dash_table.DataTable(id='base_settings_table',
                             columns=[{"name": name, "id": str(i-1), "editable": (i!= 0)} for i,name in enumerate(SettingsTableFunctions.table_columns_base_settings)],
                             data=[],
                             style_header={'backgroundColor': 'rgb(230, 230, 230)',
                                           'fontWeight': 'bold'
                                           },
                             style_cell={'height': 'auto',
                                         # all three widths are needed
                                         'minWidth': '3%','width': '3%', 'maxWidth': '3%',
                                         'whiteSpace': 'normal',
                                         },
                             style_data_conditional=[{'if': {'row_index':   1 },'border_top':'0px'},
                                                     {'if': {'row_index':   3 },'border_top':'0px'},
                                                     {'if': {'row_index':   5 },'border_top':'0px'},
                                                     ],
                             style_cell_conditional=[{'if': {'column_id': '-1'},'width': '15%'},
                                                     {'if': {'column_id': '-1'},'textAlign': 'left'}],
                             ),

        dash_table.DataTable(id='derived_settings_table',
                             editable=False,
                             columns=[{"name": name, "id": str(i-1)} for i,name in enumerate(SettingsTableFunctions.table_columns_derived_settings)],
                             data=[],
                             style_header={'backgroundColor': 'rgb(230, 230, 230)',
                                           'fontWeight': 'bold',
                                           'color':'black',
                                           },
                             style_cell={'height': 'auto',
                                         # all three widths are needed
                                         'minWidth': '3%','width': '3%', 'maxWidth': '3%',
                                         'whiteSpace': 'normal',
                                         'color':'gray',
                                         },
                             style_data_conditional=[{'if': {'row_index':   1 },'border_top':'0px'},
                                                     {'if': {'row_index':   3 },'border_top':'0px'},
                                                     ],
                             style_cell_conditional=[{'if': {'column_id': '-1'},'width': '15%'},
                                                     {'if': {'column_id': '-1'},'textAlign': 'left'},
                                                     {'if': {'column_id': '-1'},'color': 'black'}],
                             ),
        html.Div(children=[
                html.P('''* Units: "BG" stands for md/dL.'''),
                html.P('''** The two numbers in each hour column represent "on the hour" (top) and "on the half-hour" (bottom).'''),
                html.P('''*** "True basal rate" represents what your basal insulin should be, based on your sensitivity and liver glucose settings.'''),
                ]),

        ] # html.Div Children
    ) # html.Div

#
# Upload callback (new)
#
@app.callback(Output('uploaded-input-data-flag', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_file(list_of_contents, list_of_names, list_of_dates):

    output = LoadNewFile.LoadNewFile(list_of_contents, list_of_names, list_of_dates, my_globals)
    ManageSettings.LoadFromJsonData(my_globals)

    return output

#
# Update the plot
#
@app.callback(Output('display-tidepool-graph', 'figure'),
              [Input('uploaded-input-data-flag', 'children'),
               Input('show-this-day','n_clicks_timestamp'),
               Input('overview-button','n_clicks_timestamp')],
              [State('my-date-picker-single', 'date'),])
def update_plot(update_flag,show_this_day,show_overview,date):

    if update_flag == None :
        # Don't worry - this will be updated by default from the Upload callback
        return {}

    start_time = my_globals['pd_smbg']['deviceTime'].iloc[-1]
    end_time   = my_globals['pd_smbg']['deviceTime'].iloc[0]

    # print('date:',date,type(date))

    if (show_this_day != None) :
        if (show_overview == None) or (show_this_day > show_overview) :
            # print('update_plot date',date)
            try :
                the_time = datetime.datetime.strptime(date,'%Y-%m-%dT%H:%M:%S')
            except ValueError :
                the_time = datetime.datetime.strptime(date,'%Y-%m-%d')
            start_time = the_time.strftime('%Y-%m-%dT04:00:00')
            end_time  = (the_time+datetime.timedelta(days=1)).strftime('%Y-%m-%dT10:00:00')

    start_time_dt = datetime.datetime.strptime(start_time,'%Y-%m-%dT%H:%M:%S')
    end_time_dt   = datetime.datetime.strptime(end_time  ,'%Y-%m-%dT%H:%M:%S')

    return ManagePlots.UpdatePlot(my_globals,start_time_dt,end_time_dt)

#
# Update the available dates
#
@app.callback(Output('my-date-picker-single', 'min_date_allowed'),
              [Input('uploaded-input-data-flag', 'children')])
def update_dates_min(update_indicator):

    return min(np.array(my_globals['pd_smbg']['deviceTime'],dtype='datetime64'))

@app.callback(Output('my-date-picker-single', 'max_date_allowed'),
              [Input('uploaded-input-data-flag', 'children')])
def update_dates_max(update_indicator):

    return max(np.array(my_globals['pd_smbg']['deviceTime'],dtype='datetime64'))

@app.callback(Output('my-date-picker-single', 'initial_visible_month'),
              [Input('uploaded-input-data-flag', 'children')])
def update_dates_month(update_indicator):

    return max(np.array(my_globals['pd_smbg']['deviceTime'],dtype='datetime64'))

@app.callback(Output('my-date-picker-single', 'date'),
              [Input('uploaded-input-data-flag', 'children')])
def update_dates_day(update_indicator):

    return max(np.array(my_globals['pd_smbg']['deviceTime'],dtype='datetime64'))

#
# Update the base table
#
@app.callback(Output('base_settings_table', 'data'),
              [Input('uploaded-input-data-flag', 'children')])
def update_base_settings(table):

    return SettingsTableFunctions.UpdateBaseTable(my_globals)

#
# Update InsulinTa
#
@app.callback(Output('insulin-decay-time', 'value'),
              [Input('uploaded-input-data-flag', 'children')])
def update_insulin_ta_inpudata(not_used):

    if not my_globals['current_setting'] :
        return 4

    return my_globals['current_setting'].getInsulinTaHrMidnight(0)

#
# User updates InsulinTa
#
@app.callback(Output('insulin-decay-time', 'type'),
              [Input('insulin-decay-time', 'value')])
def update_insulin_ta_user(ta):

    if not my_globals['current_setting'] :
        return 'text'

    if ta :
        my_globals['current_setting'].setInsulinTa(ta)
        print('Updated Insulin Ta to:',my_globals['current_setting'].getInsulinTaHrMidnight(0))

    return 'text'

#
# User updates FoodTa
#
@app.callback(Output('food-decay-time', 'type'),
              [Input('food-decay-time', 'value')])
def update_food_ta_user(ta):

    if not my_globals['current_setting'] :
        return 'text'

    if ta :
        my_globals['current_setting'].setFoodTa(ta)
        print('Updated Food Ta to:',my_globals['current_setting'].getFoodTaHrMidnight(0))

    return 'text'

#
# Update derived table
#
@app.callback(Output('derived_settings_table', 'data'),
              [Input('base_settings_table', 'data'),
               Input('insulin-decay-time', 'value')])
def update_derived_table(table,ta):

    if ta :
        my_globals['current_setting'].setInsulinTa(ta)

    return SettingsTableFunctions.UpdateDerivedTable(table,my_globals)


app.title = 'Kurt Webpage'

# This is apparently okay to deploy too.
if __name__ == '__main__':
    app.run_server(debug=True)
