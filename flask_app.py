
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
import pandas as pd
import dash_table

# needed for callbacks
from dash.dependencies import Input, Output, State

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# Make some globals that we can overwrite, refer to, etc.
my_globals = dict()
my_globals['global_df'] = 0
my_globals['pd_smbg'] = 0

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

        html.Label('User-input values:'),
        dcc.Input(id='my-id', value='initial value', type='text'),
        html.Div(id='my-div'),

        html.Label('Slider:'),
        dcc.Slider(min=0,max=9,value=5,
                   marks={i: 'Label {}'.format(i) if i == 1 else str(i) for i in range(1, 9)},
                   ), # Slider

        ] # html.Div Children
    ) # html.Div

#
# Text callback
#
@app.callback(
    Output(component_id='my-div', component_property='children'),
    [Input(component_id='my-id', component_property='value')]
)
def update_output_div(input_value):
    return 'You\'ve entered "{}"'.format(input_value)

#
# How we parse the input file contents
#
def process_input_file(contents, filename, date):

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            my_globals['global_df'] = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            my_globals['global_df'] = pd.read_excel(io.BytesIO(decoded))
        elif 'json' in filename :
            my_globals['global_df'] = pd.read_json(io.BytesIO(decoded))

    except Exception as e:
        print(e,file=sys.stdout)
        return 'There was an error processing this file.'

    return 'Using new file, named {}'.format(filename)

#
# Upload callback (new)
#
@app.callback(Output('uploaded-input-data-flag', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_file(list_of_contents, list_of_names, list_of_dates):

    text_outputs = []

    if list_of_contents is None:
        # Use the default file
        my_globals['global_df'] = pd.read_json('Tidepool_Export_191104_191110.json')
        list_of_names = ''
        list_of_dates = ''
        text_outputs = ['Using default file.']

    else :

        if type(list_of_contents) != type([]) :
            list_of_contents = [list_of_contents]

        if type(list_of_names) != type([]) :
            list_of_names = [list_of_names]

        if type(list_of_dates) != type([]) :
            list_of_dates = [list_of_dates]

        print('length of contents:',len(list_of_contents), file=sys.stdout)
        print('list of filenames:',list_of_names, file=sys.stdout)
        print('list of last_modified:',list_of_dates, file=sys.stdout)

        text_outputs = list(process_input_file(c, n, d) for c, n, d in zip(list_of_contents, list_of_names, list_of_dates))

        find_errors = list('error' in a for a in text_outputs)
        if (True in find_errors) :
            return text_outputs[find_errors.index(True)]

    print('updating global_smbg',file=sys.stdout)
    my_globals['pd_smbg'] = my_globals['global_df'][my_globals['global_df']['type'] == 'smbg'][['deviceTime', 'value']]

    return '. '.join(text_outputs)

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


app.title = 'Kurt Webpage'

# This is apparently okay to deploy too.
if __name__ == '__main__':
    app.run_server(debug=True)
