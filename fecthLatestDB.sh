cd "$(dirname "$0")"
ssh evezh 'cd seum-counter; source env/bin/activate; python manage.py dumpdata --exclude auth.permission --exclude sessions.session --exclude admin.logentry --exclude contenttypes > seum.json'
scp evezh:/home/denis/seum-counter/seum.json seum.json
rm -f db.sqlite3
source env/bin/activate
python manage.py migrate
python manage.py loaddata seum.json
