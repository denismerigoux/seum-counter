# seum-counter

## Installation

Clone the repo, then create a `virtualenv` with Python 3, then install the required packages with :

    pip install -r requirements.txt

Then copy and paste the settings file template located in folder `seum`:
```
cd seum && cp settings.py.default settings.py
```

In order to use correctly the internationalisation, compile the locale files:
```
python manage.py compilemessages
```

To  update the locale file for the project, use
```
django-admin makemessages -l fr --ignore=env
```
where `env` is the name of the folder containing your virtualenv.

## Running the server

### Developement

First, comment out the lines below "#Production settings" in `settings.py`.

You will also need to apply the unapplied migrations:

    python manage.py migrate

Then simply use the django command:

    python manage.py runserver 0.0.0.0:8000

If you want to use the Django Debug Toolbar, follow the instructions from the [https://django-debug-toolbar.readthedocs.io/en/1.6/installation.html](official documentation).  
You just have to edit your `settings.py` file.

### Production

Install the packages needed to run an Apache server with `wsgi_mod` :

    sudo apt-get install apache2 libapache2-mod-wsgi-py3

Then add the following content to the file `/etc/apache2/sites-available/000-default.conf`, inside the `<VirtualHost>` tag :

    Alias /static <path-to-project-folder>/static
    <Directory <path-to-project-folder>/static>
         Require all granted
    </Directory>

    <Directory <path-to-project-folder>/seum>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    WSGIDaemonProcess seum python-path=<path-to-project-folder>:<path-to-project-folder>/<name-of-virtualenv>/lib/python3.5/site-packages
    WSGIProcessGroup seum
    WSGIScriptAlias / <path-to-project-folder>/seum/wsgi.py

To give Apache the permission to serve the files, execute these three commands :

    chmod 664 <path-to-project-folder>/db.sqlite3
    sudo chown :www-data <path-to-project-folder>/db.sqlite3
    sudo chown :www-data <path-to-project-folder>

To launch or restart the server, simply run :

    sudo service apache2 restart

### Backup data

To backup the database, execute the command

    python manage.py dumpdata --exclude contenttypes > seum.json

You can then restore your data into a freshly migrated new database with

    python manage.py loaddata seum.json
