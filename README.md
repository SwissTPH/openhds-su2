openhds-su2
===========

A web-based openHDS progress and quality monitoring tool. To be used with the server components of the [openhds platform](https://github.com/SwissTPH/) 

###Installation (gunicorn on Ubuntu)

```
git clone https://github.com/SwissTPH/openhds-su2.git
cd openhds-su2/
sudo apt-get install python-virtualenv python-pip libmysqlclient-dev libxml2-dev libxslt-dev python-dev
virtualenv env
source env/bin/activate
easy_install -U distribute
python setup.py install
gunicorn -b 0.0.0.0:4000 su2:app
```
