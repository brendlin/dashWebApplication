
from dash_table import DataTable

columns = [['IsBWZ','IsBWZ'],
           ['Class','Event type'],
           ['iov_0_utc','Start time'],
           ['duration','Duration (hr)'],
           ['magnitude','Magnitude'],
           ]

container_opts = ['Add an event','Food','LiverFattyGlucose','ExerciseEffect']

# Exercise: start time, duration, Magnitude, unit
# Food: start time, ta, Magnitude, unit
# fatty glucose: start time (according to temp basal), duration (according to temp basal), (magnitude) percent (according to temp basal) unit (percent)

container_table = DataTable(id='container-table',
                            columns=[{'name':i[1], 'id':i[0], 'presentation':('dropdown' if i[0] == 'Class' else 'input'),'deletable': False,} for i in columns],
                            data=[{'iov_0_utc':'January 1970','iov_1_utc':'March 2019','IsBWZ':'0','Class':'Add an event','unit':'%','magnitude':'30','duration':1.6}],
                            editable=True,
                            row_deletable=True,
                            # hide IsBWZ, which you need to see if it should be editable
                            style_cell={'height': '35px'},
                            style_cell_conditional=[{'if': {'column_id': 'IsBWZ'},'display': 'none'},
                                                    {'if': {'column_id': 'Class'},'textAlign': 'left'},
                                                    {'if': {'column_id': 'iov_0_utc'},'textAlign': 'left'},
                                                    {'if': {'column_id': 'magnitude' },'border_right':'0px'},
                                                    ],
                            dropdown_conditional=[{'if': {'column_id': 'Class',
                                                          'filter_query': '{IsBWZ} eq "0"'},
                                                   'options': list({'label': i, 'value': i} for i in container_opts),
                                                   'clearable':False,
                                                   },
                                                  ],
                            )

container_table_units = DataTable(id='container-table-units',
                                  columns=[{'name':'', 'id':'unit'}],
                                  data=[{'unit':'g'}],
                                  style_cell={'height': '35px','border_left':'0px'},
                                  )
