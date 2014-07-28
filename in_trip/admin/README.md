#dependency
see requirements.txt file

#install instructions
``` bash
$ pip install -r requirements.txt
$ cp config/config.py.template config/config.py
$ cp config/uwsgi.ini.template config/uwsgi.ini
```
then edit config/config.py, change MONGO_DB and PORT variables;
     edit config/uwsgi.ini, change the path;
run `python websetup.py`.
