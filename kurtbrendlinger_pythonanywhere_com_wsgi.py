# This file contains the WSGI configuration required to serve up your
# web application at http://<your-username>.pythonanywhere.com/
# It works by setting the variable 'application' to a WSGI handler of some
# description.
#
# The below has been auto-generated for your Flask project

import sys

# add your project directory to the sys.path
project_home = u'/home/kurtbrendlinger/dashWebApplication'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# import flask app but need to call it "application" for WSGI to work
#from flask_app import app as application  # noqa

# The above is modified to accommodate a Dash application
from app import app
from dashWebApplication.LayoutT1D import layout
app.layout = layout
app.title = 'T1D Dashboard'
application = app.server

# Hopefully this file does not need to be updated very often.
