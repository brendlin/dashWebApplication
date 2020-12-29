
Setting up on pythonAnywhere
==================================

```bash
cd $HOME; # this corresponds to /home/kurtbrendlinger
mkvirtualenv dashappenv --python=/usr/bin/python3.7
pip install -r mysite/requirements3.7.txt
```

Next, you have to set up the app on pythonAnywhere:
 - A good resource is this: https://csyhuang.github.io/2018/06/24/set-up-dash-app-on-pythonanywhere/
 - Start a new web app, and specify that it is a Flask app. Use python 3.7.
 - Specify the location of your virtual environment in the web area.
 - Edit your WSGI file:

```
from dashing_demo_app import app
application = app.server
```

A note on the pythonAnywhere disk filling up:
========================
In case your pythonAnywhere account is filling up, you can remove the pip folder in the `.cache` directory, which somehow is huge!
In the future, you can try using the `pip install --no-cache-dir` option in order to avoid this issue in the first place.

Running locally
========================

Simply do `python3 flask_app.py` to open a debug localhost server.
