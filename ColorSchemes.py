
def MakeTableGradient(rgba1,rgba2,transparency = 0.55) :
    TableGradient = []

    for i in range(10) :
        col1 = rgba1.split('(')[1].split(')')[0].split(',')
        col2 = rgba2.split('(')[1].split(')')[0].split(',')
        
        r1 = int(col1[0])
        r2 = int(col2[0])
        rdiff = int((r2-r1)*(i/9.))

        g1 = int(col1[1])
        g2 = int(col2[1])
        gdiff = int((g2-g1)*(i/9.))

        b1 = int(col1[2])
        b2 = int(col2[2])
        bdiff = int((b2-b1)*(i/9.))

        TableGradient.append('rgba(%d,%d,%d,%.2f)'%(r1+rdiff,g1+gdiff,b1+bdiff,transparency))

    return TableGradient

class DefaultColorScheme :

    CGMData = '#77B6EA'
    MeterData = '#1C2541'

    TargetBandColorGreen = 'rgba(102,224,102,0.75)'
    TargetBandColorYellow = 'rgba(255,224,102,0.75)'

    InsulinBolus      = 'rgba(153,235,153,0.8)'
    InsulinBolusAlt   = 'rgba(102,224,102,0.8)'
    Food              = 'rgba(224,102,103,0.8)'
    FoodAlt           = 'rgba(236,154,153,0.8)'
    LiverBasalGlucose = 'rgba(255,224,102,0.8)'
    BasalInsulin      = 'rgba(173,194,255,0.8)'
    LiverFattyGlucose = 'rgba(255,165,  2,0.8)' # 'Orange'
    ExerciseEffect    = 'rgba(128,  0,129,0.8)' # 'Purple'

    InsulinBolusTxt      = 'rgba(103,177,110,1)'
    FoodTxt              = 'rgba(184,107,107,1)'
    LiverBasalGlucoseTxt = 'rgba(193,174,102,1)'
    BasalInsulinTxt      = 'rgba(146,160,199,1)'
    LiverFattyGlucoseTxt = '#D0963D'
    ExerciseEffectTxt    = ExerciseEffect.replace('0.8)','1)')

    Avg17Plot     = 'rgba(78,82,128,1)'
    Avg17ErrorBar = 'rgba(78,82,128,0.5)'

    Avg4Plot     = 'rgba(173,113,3,1)'
    Avg4ErrorBar = 'rgba(255,165,2,0.5)'

    TableBackground = 'rgba(230, 230, 230, 1)'
    Transparent     = 'rgba(0,0,0,0)'

    # https://www.strangeplanet.fr/work/gradient-generator/index.php
    #TableGradient   = ["#ADC3FF", "#B1BCF2", "#B5B6E5", "#B9B0D8", "#BDAACB", "#C1A4BF", "#C59EB2", "#C998A5", "#CD9298", "#D18C8C"]

    TableGradient = MakeTableGradient('rgba(45,128,236,1)','rgba(236,42,0,1)',0.7)

class ColorScheme2 :

    # https://coolors.co/e3b505-610345-107e7d-044b7f-95190c
    Yellow = 'rgba(227, 181, 5, 1)'
    Purple = 'rgba(97, 3, 69, 1)'
    Green  = 'rgba(16, 126, 125, 1)'
    Blue   = 'rgba(4, 75, 127, 1)'
    Red    = 'rgba(149, 25, 12, 1)'
    Orange = 'rgba(206, 81, 4, 1)'

    LGreen = 'rgba( 59, 149, 148, 1)' #3B9594
    LRed   = 'rgba(187, 108, 100, 1)' #BB6C64

    CGMData = Blue
    MeterData = '#1C2541'

    TargetBandColorGreen = Green.replace('1)','0.75)')
    TargetBandColorYellow = Yellow.replace('1)','0.75)')

    InsulinBolusTxt      = Green
    InsulinBolusAltTxt   = LGreen
    FoodTxt              = Red
    FoodAltTxt           = LRed
    LiverBasalGlucoseTxt = Yellow
    BasalInsulinTxt      = Blue
    LiverFattyGlucoseTxt = Orange
    ExerciseEffectTxt    = Purple

    InsulinBolus      = InsulinBolusTxt     .replace('1)','0.8)')
    Food              = FoodTxt             .replace('1)','0.8)')
    LiverBasalGlucose = LiverBasalGlucoseTxt.replace('1)','0.8)')
    BasalInsulin      = BasalInsulinTxt     .replace('1)','0.8)')
    LiverFattyGlucose = LiverFattyGlucoseTxt.replace('1)','0.8)')
    ExerciseEffect    = ExerciseEffectTxt   .replace('1)','0.8)')

    Avg17Plot     = Blue
    Avg17ErrorBar = Blue.replace('1)','0.4)')

    Avg4Plot     = Orange
    Avg4ErrorBar = Orange.replace('1)','0.4)')

    TableBackground = 'rgba(230, 230, 230, 1)' # gray
    Transparent     = 'rgba(0,0,0,0)'    

    TableGradient = MakeTableGradient(Blue,Red)

ColorScheme = DefaultColorScheme


