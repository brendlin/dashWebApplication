import sys
import pandas as pd

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
# For the upload callback (uses process_input_file)
#
def LoadNewFile(list_of_contents, list_of_names, list_of_dates, globals) :
    text_outputs = []

    if list_of_contents is None:
        # Use the default file
        globals['global_df'] = pd.read_json('download.json')
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

    data = globals['global_df']
    globals['pd_smbg'] = data[data['type'] == 'smbg'][['deviceTime', 'value']]

    return '. '.join(text_outputs)
