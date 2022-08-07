
# This file is special in the sense that it needs to be called app,
# and needs to contain the dash.Dash instance which is also called app.
# (Other projects will be looking for an object called "app" in the current working directory)

import dash
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# Note that you need __name__ here, otherwise the production version
# cannot find the assets directory.
app = dash.Dash(__name__,external_stylesheets=external_stylesheets,
                suppress_callback_exceptions=True)
