
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
 - Your WSGI file should be in this package -- simply link it to the appropriate place:
```bash
ln -s kurtbrendlinger_pythonanywhere_com_wsgi.py /var/www/kurtbrendlinger_pythonanywhere_com_wsgi.py
```
 - Don't forget to make sure that the "WSGI configuration file" is set to this path.
 - Finally, your *static files* are the ones (like the favicon and the spinner) are in the `assets` directory. In the PythonAnywhere web dashboard, make sure to:
    - Link (or copy) the assets you want into the `$HOME/assets` directory (this is because your *working directory* is $HOME)
    - specify `$HOME/assets` as your static file path.
 - You can also specify the css file that you use as a static file -- presumably this will speed up the loading.

A note on the pythonAnywhere disk filling up:
========================
In case your pythonAnywhere account is filling up, you can remove the pip folder in the `.cache` directory, which somehow is huge!
In the future, you can try using the `pip install --no-cache-dir` option in order to avoid this issue in the first place.

Running locally
========================

Simply do `python3 flask_app.py` to open a debug localhost server.

Getting Tidepool data:
========================

Make sure the correct username/password are indicated in token.txt. Then do:
```
source JSONDownload.sh
```
