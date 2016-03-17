# seum-counter

## Installation

Clone the repo, then create a `virtualenv` with Python 3, then install the required packages with :

    pip install -r requirements.txt

## Running the server

### Developement

Simply use the django command :

    python manage.py runserver 0.0.0.0:8000

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
