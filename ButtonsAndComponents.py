
from dash import dcc
from dash import html

from .Utils import sandbox_date

upload_data_button = html.Button('Upload from Tidepool',
                                 style={'width':'95%','display':'table-cell'},
                                 )

upload_data = dcc.Upload(id='upload-data',
                         children=[upload_data_button],
                         multiple=False,
                         style={'width':'300px','display':'table-cell'},
                         )

upload_libre_button = html.Button('Upload from Libre',
                                  style={'width':'95%','display':'table-cell'},
                                  )

upload_libre = dcc.Upload(id='upload-libre',
                          children=[],
                          multiple=False,
                          style={'width':'25%','display':'table-cell'},
                          )

analy_mode_dropdown = dcc.Dropdown(id='analysis-mode-dropdown',
                                   options=[{'label':'Overview Mode','value':'data-overview'},
                                            {'label':'Daily Analysis Mode','value':'daily-analysis'},
                                            {'label':'Sandbox Mode','value':'sandbox'},
                                            {'label':'CGM Performance','value':'cgm-plot'},
                                            ],
                                   value='data-overview',
                                   style={'width':'200px','display': 'inline-block','verticalAlign':'middle'},
                                   searchable=False,
                                   )

date_picker = dcc.DatePickerSingle(id='my-date-picker-single',
                                   min_date_allowed=sandbox_date,
                                   max_date_allowed=sandbox_date,
                                   initial_visible_month=sandbox_date,
                                   date=sandbox_date,
                                   disabled=True,
                                   )

main_graph = dcc.Graph(id='display-tidepool-graph',
                                      #config={'staticPlot':True,},
                                      figure={'layout':{'margin':{'l':60, 'r':20, 't':27, 'b':20},
                                                        'paper_bgcolor':'White','plot_bgcolor':'White',
                                                        'yaxis':{'title':'BG (mg/dL)','range':[50,300],'linecolor':'Black','mirror':'ticks','hoverformat':'0.0f',},
                                                        'xaxis':{'range':[1,100],'linecolor':'Black','mirror':'ticks'},
                                                        }
                                              },
                                      style={'height': 400,}
                                      )

containers_dropdown = dcc.Dropdown(id='containers-dropdown',
                                   placeholder='Daily events',
                                   style={'width':'220px','display':'inline-block','verticalAlign':'middle'},
                                   searchable=False
                                   )

add_rows = html.Button('Add row',
                       id='add-rows-button',
                       n_clicks=0,
                       style={'display':'table-cell','verticalAlign':'middle'}
                       )

allow_insulin = dcc.Checklist(id='allow-insulin',
                              options=[{'label':'Allow edits to insulin, BG measurements, temp basal, etc.','value':'allow-insulin'}],
                              value=['allow-insulin']
                              )

storage = [
    # Saved profiles (panda)
    html.Div(id='active-profile'    ,style={'display': 'none'},children=None), # This will store the json text
    html.Div(id='profiles-from-data',style={'display': 'none'},children=None), # This will store the json text
    html.Div(id='custom-profiles'   ,style={'display': 'none'},children=None), # This will store the json text
    html.Div(id='bwz-profile'       ,style={'display': 'none'},children=None), # This will store the json text

    # Saved container profiles
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

    # Stuff to store the state of a dropdown while a different analysis is chosen
    html.Div(id='last-profile-selected'    ,style={'display': 'none'},children=None),
    ]
