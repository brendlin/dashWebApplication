import sys
import copy
from dash import dash_table
from BGModel import Settings
from .ColorSchemes import ColorScheme

#
# Set up the table columns, and the "vanilla" settings
#
table_columns_base_settings = ['Base Settings (editable)'] + list('%02d:00'%(a) for a in range(0,24))
table_columns_derived_settings = copy.copy(table_columns_base_settings)
table_columns_derived_settings[0] = 'Derived Settings'

table_default_base_settings = []
defaults_base = (('Insulin sens. (BG/u)',50),
                 ('',50),
                 ('Food sens. (BG/g)',3.33),
                 ('',3.33),
                 ('Liver glucose (BG/hr)',50),
                 ('',50))

for row in defaults_base :
    table_default_base_settings.append(dict())
    table_default_base_settings[-1][-1] = row[0]
    for i in range(24) :
        table_default_base_settings[-1][i] = row[1]

#gradient =     ["#776BFF", "#8168EC", "#8B66D9", "#9663C6", "#A061B3", "#AA5EA0", "#B55C8D", "#BF597A", "#C95767", "#D45555"] # len 10
gradient = ColorScheme.TableGradient
bin_edges = {0:[0] + list(range(45,90,5))+[900], # len 11
             1:[0] + list(range(45,90,5))+[900], # len 11
             2:[0.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.4, 4.8, 5.2, 5.6, 900], # len 11
             3:[0.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.4, 4.8, 5.2, 5.6, 900], # len 11
             4:[0] + list(range(45,90,5))+[900],
             5:[0] + list(range(45,90,5))+[900]}

bin_edges_der = {0:[0] + list(range(12,30,2))+[900], # len 11
                 1:[0] + list(range(12,30,2))+[900], # len 11
                 2:[0.0, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 900], # len 11
                 3:[0.0, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 900], # len 11
                 }

table_color_rules = []
for i,color in enumerate(gradient) :
    for column in range(24) :
        for row in range(6) :
            table_color_rules.append({'if': {'row_index':row,'column_id':str(column),
                                             'filter_query':'%.1f <= {%d} && {%d} < %.1f'%(bin_edges[row][i],column,column,bin_edges[row][i+1])},
                                      'backgroundColor':gradient[i]})

table_color_rules_der = []
for i,color in enumerate(gradient) :
    for column in range(24) :
        for row in range(4) :
            table_color_rules_der.append({'if': {'row_index':row,'column_id':str(column),
                                                 'filter_query':'%.1f <= {%d} && {%d} < %.1f'%(bin_edges_der[row][i],column,column,bin_edges_der[row][i+1])},
                                          'backgroundColor':gradient[i]})

tmp1 = dash_table.DataTable(id='base_settings_table',
                 columns=[{"name": name, "id": str(i-1), "editable": (i!= 0)} for i,name in enumerate(table_columns_base_settings)],
                 data=[],
                 style_header={'backgroundColor': ColorScheme.TableBackground,
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
                                         ] + table_color_rules,
                 style_cell_conditional=[{'if': {'column_id': '-1'},'width': '15%'},
                                         {'if': {'column_id': '-1'},'textAlign': 'left'}],
                 )
base_settings_table = tmp1

tmp2 = dash_table.DataTable(id='derived_settings_table',
                 editable=False,
                 columns=[{"name": name, "id": str(i-1)} for i,name in enumerate(table_columns_derived_settings)],
                 data=[],
                 style_header={'backgroundColor': 'rgb(230, 230, 230)',
                                          'fontWeight': 'bold',
                               'color':'black',
                               },
                 style_cell={'height': 'auto',
                             # all three widths are needed
                             'minWidth': '3%','width': '3%', 'maxWidth': '3%',
                             'whiteSpace': 'normal',
                             #'color':'gray',
                             },
                 style_data_conditional=[{'if': {'row_index':   1 },'border_top':'0px'},
                                         {'if': {'row_index':   3 },'border_top':'0px'},
                                         ] + table_color_rules_der,
                 style_cell_conditional=[{'if': {'column_id': '-1'},'width': '15%'},
                                         {'if': {'column_id': '-1'},'textAlign': 'left'},
                                         {'if': {'column_id': '-1'},'color': 'black'}],
                 )
derived_settings_table = tmp2

#------------------------------------------------------------------
def UpdateBaseTable(the_userprofile_json) :

    if not the_userprofile_json :
        return table_default_base_settings

    the_userprofile = Settings.TrueUserProfile.fromJson(the_userprofile_json)

    out_table = []
    for row in defaults_base :
        out_table.append(dict())
        out_table[-1][-1] = row[0]

    fcns = ['InsulinSensitivity','FoodSensitivity','LiverHourlyGlucose']
    round_digits = [0,1,0]
    sign = [-1,1,1]
    for column in range(3) :

        for i in range(24) :
            on_the_hour = getattr(the_userprofile,'get%sHrMidnight'%(fcns[column]))(i)
            half_hour   = getattr(the_userprofile,'get%sHrMidnight'%(fcns[column]))(i+0.5)

            round_on_the_hour = sign[column]*round(on_the_hour,round_digits[column])
            round_half_hour   = sign[column]*round(half_hour  ,round_digits[column])

            if not round_digits[column] :
                round_on_the_hour = int(round_on_the_hour)
                round_half_hour   = int(round_half_hour  )

            # half-hour increments are one row down
            out_table[column*2  ][i] = str(round_on_the_hour)
            out_table[column*2+1][i] = str(round_half_hour  )

    return out_table

#------------------------------------------------------------------
def UpdateDerivedTable(table,insulin_decay_time):

    #print(table,file=sys.stdout)

    i_isens = 0
    i_fsens = 1
    i_liver = 2

    # get the duration (needed for basal)
    # divide by 2 (peak is ta/2), multiply by 2 (1/2hr increments)
    offset = int(float(insulin_decay_time))

    ret = []

    sens,fsens,liver = [],[],[]

    # convert back to 48-entry lists
    for i in range(24) :

        for j in range(2) :
            try :
                sens.append( float( table[i_isens*2+j][str(i)] ) )
            except ValueError :
                sens.append(None)

        for j in range(2) :
            try :
                fsens.append( float( table[i_fsens*2+j][str(i)] ) )
            except ValueError :
                fsens.append(None)

        for j in range(2) :
            try :
                liver.append( float( table[i_liver*2+j][str(i)] ) )
            except ValueError :
                liver.append(None)

    basal48,ric48 = [],[]

    # calculate stuff (using 48-length lists)
    for i in range(48) :
        try :
            ric48.append( int( round( sens[i]/float(fsens[i]),0) ) )
        except (TypeError, ZeroDivisionError) as e:
            ric48.append('ERR')

        i_offset = (i+offset)%48

        try :
            # round to the nearest 0.25
            basal48.append( round( 40*liver[i_offset]/float(sens[i])) /40. )
        except (TypeError, ZeroDivisionError) as e:
            basal48.append('ERR')

    # populate the rows
    ric_hr,ric_hhr = dict(),dict()
    basal_hr,basal_hhr = dict(),dict()

    ric_hr['-1'] = 'Carb-insulin ratio (g/u)'
    ric_hhr['-1'] = ''

    basal_hr,basal_hhr = dict(),dict()
    basal_hr['-1']  = 'True basal rate (u/hr)'
    basal_hhr['-1'] = ''

    for i in range(24) :
        ric_hr [str(i)] = ric48[i*2  ]
        ric_hhr[str(i)] = ric48[i*2+1]

        basal_hr [str(i)] = basal48[i*2  ]
        basal_hhr[str(i)] = basal48[i*2+1]

    ret.append(ric_hr)
    ret.append(ric_hhr)
    ret.append(basal_hr)
    ret.append(basal_hhr)

    return ret

#------------------------------------------------------------------
def ConvertBaseTableToProfile(table,ta,tf) :

    sensitivities = [0]*48
    foodsens = [0]*48
    liver = [0]*48

    the_userprofile = Settings.TrueUserProfile()

    for i in range(24) :
        # on the hour
        the_userprofile.InsulinSensitivity[i*2] = -int(table[0][str(i)])
        the_userprofile.FoodSensitivity[i*2]    = float(table[2][str(i)])
        the_userprofile.LiverHourlyGlucose[i*2] = int(table[4][str(i)])
        the_userprofile.InsulinTa[i*2]          = ta
        the_userprofile.FoodTa[i*2]             = tf

        # on the half-hour
        the_userprofile.InsulinSensitivity[i*2+1] = -int(table[1][str(i)])
        the_userprofile.FoodSensitivity[i*2+1]    = float(table[3][str(i)])
        the_userprofile.LiverHourlyGlucose[i*2+1] = int(table[5][str(i)])
        the_userprofile.InsulinTa[i*2+1]          = ta
        the_userprofile.FoodTa[i*2+1]             = tf

    return the_userprofile.toJson()
