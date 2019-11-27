
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

import base64
import datetime
import io

import numpy as np
import dash_table

# Tools
import ManageSettings
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

        html.Label('Insulin decay time (hr): '),
        dcc.Input(id='insulin-decay-time', value='4', type='text'),
        html.Label('Food decay time (hr): '),
        dcc.Input(id='food-decay-time', value='2', type='text'),

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
                             style_cell_conditional=[{'if': {'column_id': '-1'},'width': '15%'},
                                                     {'if': {'column_id': '-1'},'textAlign': 'left'},
                                                     {'if': {'column_id': '-1'},'color': 'black'}],
                             ),
        html.Div(children=[
                html.P('''* Units: "BG" stands for md/dL.'''),
                html.P('''** To split a setting int two half-hour increments, type e.g. '50/60'.'''),
                html.P('''*** "True basal rate" represents what your basal insulin should be, based on your sensitivity and liver glucose settings.'''),
                ]),

        html.Label('Slider:'),
        dcc.Slider(min=0,max=9,value=5,
                   marks={i: 'Label {}'.format(i) if i == 1 else str(i) for i in range(1, 9)},
                   ), # Slider

        ] # html.Div Children
    ) # html.Div

#
# Text callback
#
# @app.callback(
#     Output(component_id='my-div', component_property='children'),
#     [Input(component_id='my-id', component_property='value')]
# )
# def update_output_div(input_value):
#     return 'You\'ve entered "{}"'.format(input_value)

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
              [Input('uploaded-input-data-flag', 'children')])
def update_plot(update_indicator):

    if update_indicator == None :
        # Don't worry - this will be updated by default from the Upload callback
        return {}

    print('children:',update_indicator,file=sys.stdout)
    print(my_globals['pd_smbg'][:10],file=sys.stdout)
    print('first device time:',my_globals['pd_smbg']['deviceTime'].iloc[0],file=sys.stdout)

    return {'data': [
            {'x': my_globals['pd_smbg']['deviceTime'], 'y': np.round(my_globals['pd_smbg']['value']*18.01559), 'type': 'scatter', 'name': 'SF','mode':'markers'},
            ],
            'layout': {'title': 'Default for None'
                       }
            }

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

    my_globals['current_setting'].setFoodTa(ta)
    print('Updated Food Ta to:',my_globals['current_setting'].getFoodTaHrMidnight(0))
    return 'text'

#
# Update derived table
#
@app.callback(Output('derived_settings_table', 'data'),
              [Input('base_settings_table', 'data')])
def update_derived_table(table):

    return SettingsTableFunctions.UpdateDerivedTable(table,my_globals)


app.title = 'Kurt Webpage'

# This is apparently okay to deploy too.
if __name__ == '__main__':
    app.run_server(debug=True)
