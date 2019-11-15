
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

import pandas as pd
import dash_table

# needed for callbacks
from dash.dependencies import Input, Output, State

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# start out with some data
global_df = pd.read_json('Tidepool_Export_191104_191110.json')

global_smbg = global_df[global_df['type'] == 'smbg'][['deviceTime', 'value']][:5]

#print(global_df[global_df['type'] == 'smbg'][['deviceTime', 'value']][:5],file=sys.stdout)

# for deployment, pass app.server (which is the actual flask app) to WSGI etc
app = dash.Dash(external_stylesheets=external_stylesheets)

app.layout = html.Div(
    children=[
#     html.Link(rel="icon", href="images/shortcut2.png"),

        html.H1(children='Modeling blood glucose and the effects of insulin'),

        html.Div(children='''
Upload your data below:
'''
                 ),

        dcc.Upload(id='upload-data',
                   children=html.Div(['Drag and Drop or ',html.A('Select Files')]),
                   style={'width': '100%',
                          'height': '60px',
                          'lineHeight': '60px',
                          'borderWidth': '1px',
                          'borderStyle': 'dashed',
                          'borderRadius': '5px',
                          'textAlign': 'center',
                          'margin': '10px'
                          },
                   # Allow multiple files to be uploaded
                   multiple=False
                   ),

        html.Div(id='output-data-upload',children = [
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
def parse_contents(contents, filename, date):
    # return html.Div(children = 'Hello there!')
    content_type, content_string = contents.split(',')

    #print(content_string[:300],file=sys.stdout)

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            global_df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            global_df = pd.read_excel(io.BytesIO(decoded))
        elif 'json' in filename :
            global_df = pd.read_json(io.BytesIO(decoded))

    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    df_smaller = global_df[['deviceTime','value','subType']]
    data_dict = df_smaller.to_dict('records')
    #print(data_dict,file=sys.stdout)

    # return the figure feature of the graph
    return {'data': [{'x': [1, 2, 3], 'y': [2, 2, 2], 'type': 'scatter', 'name': 'Montreal updated!'},
                     ],
            'layout': {'title': 'UPDATED'}
            }

#
# Upload callback
#
@app.callback(Output('display-tidepool-graph', 'figure'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):

    if list_of_contents is None:
        return {'data': [#{'x': global_smbg['deviceTime'], 'y': global_smbg['value'], 'type': 'scatter', 'name': 'SF','mode':'markers'},
                {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'scatter', 'name': 'defaultreal'},
                {'x': [1, 2, 3], 'y': [5, 3, 2], 'type': 'scatter', 'name': 'Defaultreal 2'},
                ],
                'layout': {'title': 'Default for None'
                           }
                }

    if list_of_contents is not None:

        if type(list_of_contents) != type([]) :
            list_of_contents = [list_of_contents]

        if type(list_of_names) != type([]) :
            list_of_names = [list_of_names]

        if type(list_of_dates) != type([]) :
            list_of_dates = [list_of_dates]

        print('length of contents:',len(list_of_contents), file=sys.stdout)
        print('list of filenames:',list_of_names, file=sys.stdout)
        print('list of last_modified:',list_of_dates, file=sys.stdout)

        children = [
            parse_contents(c, n, d) for c, n, d in zip(list_of_contents, list_of_names, list_of_dates)
            ]
        return children[0]

app.title = 'Kurt Webpage'

# This is apparently okay to deploy too.
if __name__ == '__main__':
    app.run_server(debug=True)
