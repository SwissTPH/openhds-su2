Run report generator

python lib/generateReports.py

Su2 deploy (on Ubuntu 12.04), common steps

Assumes openHDS, ODKAggregate are set up on the server.
Assumes the package is installed in /home/data/openhds-su2/, if installed in another location,
at least /etc/su2.conf and su2.wsgi need to be adapted.

$sudo apt-get install libapache2-mod-wsgi
$sudo apt-get install libmysqlclient-dev
$sudo apt-get install libxml2-dev libxslt-dev
$sudo apt-get install python-virtualenv python-pip

$cd /home/data/
$unzip PATH_TO_ZIP/openhds-su2.zip

$cd opnhds-su2
$virtualenv env
$source env/bin/activate
$easy_install -U distribute
$python setup.py install

Edit config.py, set host specific parameters

Su2 deploy (on Ubuntu 12.04), using gunicorn

gunicorn is installed as a prequisite in the install step above. Start the server on port 9000:

$cd /home/data/opnhds-su2
$source env/bin/activate
$gunicorn -b 0.0.0.0:4000 su2:app

Su2 deploy (on Ubuntu 12.04), using apache's wsgi module:

Configure apache. This assumes we want the application to listen on port 9000.

Copy etc/su2.conf to /etc/apache2/sites-available/su2.conf

$a2ensite su2.conf

Edit /etc/apache2/apache2.conf, add:
ServerName localhost
WSGIApplicationGroup %{GLOBAL}

$sudo /etc/init.d apache2 restart
