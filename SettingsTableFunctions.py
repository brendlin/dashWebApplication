import sys

def UpdateDerivedTable(table):

    print(table,file=sys.stdout)

    i_isens = 0
    i_fsens = 1
    i_liver = 4

    ret = []
    ric = dict()
    ric['-1'] = 'Carb-insulin ratio (g/u)'

    basal = dict()
    basal['-1'] = 'True basal rate (u/hr)'

    for i in range(24) :
        try :
            ric[str(i)] = round(float(table[i_isens][str(i)])/float(table[i_fsens][str(i)]),1)
        except (ValueError,TypeError) as e :
            ric[str(i)] = 'ERR'

        try :
            basal[str(i)] = round(float(table[i_isens][str(i)])/float(table[i_liver][str(i)]),1)
        except (ValueError,TypeError) as e :
            basal[str(i)] = 'ERR'

    ret.append(ric)
    ret.append(basal)

    return ret
