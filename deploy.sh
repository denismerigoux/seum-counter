git pull
source env/bin/activate
python manage.py compilemessages > /dev/null
sudo service apache2 reload
