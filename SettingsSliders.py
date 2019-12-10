import dash_core_components as dcc
import dash_html_components as html
from BGModel import Settings

hsliders = "40px"
hecho = "20px"

slider_divs = []

bufferLeftEcho = [html.Div(style = {"height":hecho,'width': 'calc(6% + 60px)','display':'inline-block'})]

bufferLeftSlider = dict()
for setting in ['sensitivity','food','liver'] :

    label = {'sensitivity':'Ins. Sens. (BG/u)',
             'food'       :'Food Sens. (BG/g)',
             'liver'      :'Liver glucose (BG/hr)',
             }.get(setting)

    bufferLeftSlider[setting] = [html.P(label,style={'display':'inline-block','height':hsliders,'width': 'calc(6% + 60px)','vertical-align':'middle'})]

defaults = {'sensitivity':[50,25,100,1],
            'food':[3.3,2,5,0.1],
            'liver':[50,25,100,1],
            }

# starting-point for echos-master
for setting in ['sensitivity','food','liver'] :

    sliders = list(html.Div(style = {"height":hsliders,'width': '2.4%','display':'inline-block'},
                            children = dcc.Slider(id='slider-%s-%d'%(setting,i),
                                                  value=defaults[setting][0],
                                                  min=defaults[setting][1],
                                                  max=defaults[setting][2],
                                                  step=defaults[setting][3],
                                                  updatemode='mouseup', # only 'drag' if fast
                                                  vertical=True,
                                                  included=False,
                                                  dots=False,
                                                  tooltip={'always_visible':True,'placement':'top'},
                                                  ),
                            ) for i in range(24))

    sliders_master = html.Div(style = {'height':'65px','vertical-align':'top'},
                              children = bufferLeftSlider[setting] + sliders
                              )
    slider_divs.append(sliders_master)

slider_times = list(html.Div(id='slider-times-%d'%(i),
                             style = {"height": "20px",'width': '2.4%','display':'inline-block'},
                             children = str((i+6)%24)+'h',
                             ) for i in range(24))

slider_times_master = html.Div(style = {'height':hecho},
                               children = bufferLeftEcho + slider_times
                               )

slider_divs.append(slider_times_master)

#------------------------------------------------------------------
def UpdateListOfEchos(setting,*args) :
    echos = list(html.Div(id='slider-echo-%s-%d'%(setting,i),
                          style = {"height": "20px",'width': '2.4%','display':'inline-block'},
                          children=args[i],
                          ) for i in range(24))

    return bufferLeftEcho + echos

#------------------------------------------------------------------
def UpdateSlider(setting,i,the_userprofile_json) :

    the_userprofile = Settings.TrueUserProfile.fromJson(the_userprofile_json)

    fcn = {'sensitivity':'getInsulinSensitivityHrMidnight',
           'food':'getFoodSensitivityHrMidnight',
           'liver':'getLiverHourlyGlucoseHrMidnight',
           }.get(setting)

    sign = {'sensitivity':-1,
            'food':1,
            'liver':1,
            }.get(setting)

    round_digits = {'sensitivity':0,
                   'food':1,
                   'liver':0,
                   }.get(setting)

    result = sign*getattr(the_userprofile,fcn)((i+6)%24)
    result = round(result,round_digits)
    if not round_digits :
        result = int(result)

#     print('i is',i,'hour is',(i-6)%24,'value is',result)

    return result

#------------------------------------------------------------------
def ConvertSlidersToProfile(ta,tf,sliders) :

    the_userprofile = Settings.TrueUserProfile()

    i_sens = 0
    i_food = 1
    i_liver = 2

    for i in range(24) :

        # output i, because we have this stupid 6-hour offset.
        io = ((i+6)*2)%48

        the_userprofile.InsulinSensitivity[io] = -int(sliders[24*i_sens + i])
        the_userprofile.FoodSensitivity[io]    = float(sliders[24*i_food + i])
        the_userprofile.LiverHourlyGlucose[io] = int(sliders[24*i_liver + i])
        the_userprofile.InsulinTa[io]          = ta
        the_userprofile.FoodTa[io]             = tf

        # on the half-hour (just the same as above)
        the_userprofile.InsulinSensitivity[io+1] = -int(sliders[24*i_sens + i])
        the_userprofile.FoodSensitivity[io+1]    = float(sliders[24*i_food + i])
        the_userprofile.LiverHourlyGlucose[io+1] = int(sliders[24*i_liver + i])
        the_userprofile.InsulinTa[io+1]          = ta
        the_userprofile.FoodTa[io+1]             = tf

    return the_userprofile.toJson()
