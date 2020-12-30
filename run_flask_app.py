
from app import app

import sys
sys.path.insert(0, "../")

from dashWebApplication.LayoutT1D import layout

# This is apparently okay to deploy too.
if __name__ == '__main__':
    app.title = 'T1D Dashboard'
    app.layout = layout
    app.run_server(debug=True)
