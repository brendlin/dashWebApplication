import sys
import copy

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


#------------------------------------------------------------------
def UpdateBaseTable(globals) :

    if not globals['current_setting'] :
        return table_default_base_settings

    out_table = []
    for row in defaults_base :
        out_table.append(dict())
        out_table[-1][-1] = row[0]

    fcns = ['InsulinSensitivity','FoodSensitivity','LiverHourlyGlucose']
    round_digits = [0,1,0]
    sign = [-1,1,1]
    for column in range(3) :

        for i in range(24) :
            on_the_hour = getattr(globals['current_setting'],'get%sHrMidnight'%(fcns[column]))(i)
            half_hour   = getattr(globals['current_setting'],'get%sHrMidnight'%(fcns[column]))(i+0.5)

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
def UpdateDerivedTable(table,globals):

    print(table,file=sys.stdout)

    i_isens = 0
    i_fsens = 1
    i_liver = 2

    # get the duration (needed for basal)
    # divide by 2 (peak is ta/2), multiply by 2 (1/2hr increments)
    offset = int(float(globals['current_setting'].getInsulinTaHrMidnight(0)))

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
        except TypeError :
            ric48.append('ERR')

        i_offset = (i+offset)%48

        try :
            basal48.append( round( liver[i_offset]/float(sens[i]), 1) )
        except TypeError :
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
