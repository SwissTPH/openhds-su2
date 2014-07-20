#!/usr/bin/env python

"""__init__.py: Flask-based web app"""

__email__ = "nicolas.maire@unibas.ch"
__status__ = "Alpha"

import flask
from flask import request, Response
from functools import wraps
import lib.reportLib as rL
import lib.genericReports as genRep
import MySQLdb
import MySQLdb.cursors
import json
import datetime
import os
from flask.ext.autoindex import AutoIndex


app = flask.Flask(__name__)
app.config.from_object('config')
app.debug = True

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

ai = AutoIndex(app, os.path.join(APP_ROOT, 'static/archive'), add_url_rules=False)

all_odk_forms = None
odk_event_forms = None
with open(os.path.join(APP_ROOT, 'conf', app.config['FORM_DEFINITIONS']), 'rb') as fp:
    odk_forms = json.load(fp)

all_odk_forms = odk_forms['all_forms']
odk_event_forms = odk_forms['event_forms']

period = 7
ODKCursor = None
openHDSCursor = None


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == app.config['USER'] and password == app.config['PWD']


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


#for datetime objects to date to json
def date_time_handler(obj):
    return obj.isoformat() if isinstance(obj, datetime.date) else None


@app.route('/')
@app.route('/index')
@requires_auth
def index():
    open_hds_cursor = get_db('OPEN_HDS_DB').cursor()
    individuals_today = genRep.get_individuals_where(open_hds_cursor, "COUNT(*) as count",
                                                     "membership.endDate IS null AND "
                                                     "residency.endDate IS null ", "")[0]["count"]
    total_houses = rL.query_db_one(open_hds_cursor, "SELECT COUNT(*) AS count FROM location WHERE uuid IN "
                                                    "(SELECT location_uuid FROM residency "
                                                    "WHERE endDate IS null)")["count"]
    total_households = rL.query_db_one(open_hds_cursor, "SELECT COUNT(*) AS count FROM socialgroup WHERE uuid IN "
                                                        "(SELECT socialgroup_uuid FROM membership WHERE "
                                                        "endDate IS null)")["count"]
    ops_summary = [{"name": "Number of individuals", "value": individuals_today},
                   {"name": "Number of Houses", "value": total_houses},
                   {"name": "Number of households", "value": total_households}]
    #houses = genRep.houses_with_residency(open_hds_cursor)
    filename = 'houses.kml'
    kml_file = os.path.join(APP_ROOT, "static", "tmp", filename)
    #rL.create_kml_from_container(houses, kml_file, "extId", "extId")
    return flask.render_template('index.html', opsSummary=ops_summary, filename=filename)


@app.route('/operations', methods=['GET', 'POST'])
@requires_auth
def operations():
    disp = flask.request.args.get('disp')
    if disp == 'events_by_fw':
        chart_data = genRep.get_event_rate_summary_by_fw(get_db('ODK_DB').cursor(), all_odk_forms, odk_event_forms)
    elif disp == 'events_by_type':
        chart_data = genRep.get_event_rate_summary_by_event(get_db('ODK_DB').cursor(), all_odk_forms, odk_event_forms)
    else:
        chart_data = genRep.get_operations_summary(get_db('ODK_DB').cursor(), all_odk_forms, odk_event_forms, period)
    return flask.render_template('operations.html', chart_data=json.dumps(chart_data, default=date_time_handler))


@app.route('/issues', methods=['GET', 'POST'])
@requires_auth
def issues():
    disp = flask.request.args.get('disp')
    kml_location = os.path.join(APP_ROOT, "static", "tmp")
    if disp:
        filename = disp + ".kml"
    else:
        filename = "kml.kml"
    kml_file = os.path.join(kml_location, filename)
    odk_cursor = get_db('ODK_DB').cursor()
    open_hds_cursor = get_db('OPEN_HDS_DB').cursor()
    if disp == "houses_without_visit_forms":
        data = genRep.houses_without_visit_forms(odk_cursor, all_odk_forms, open_hds_cursor)
        rL.create_kml_from_container(data, kml_file, "House ID", "House ID")
    elif disp == "duplicate_outmigrations":
        data = genRep.get_multiple_out_migrations(odk_cursor, all_odk_forms)
        #TODO
    elif disp == "duplicate_inmigrations":
        data = genRep.get_multiple_in_migrations(odk_cursor, all_odk_forms)
        #TODO
    elif disp == "duplicate_visits":
        data = genRep.get_multiple_visits(odk_cursor, all_odk_forms)
        rL.create_empty_kml(kml_file)
    elif disp == "duplicate_individuals":
        data = genRep.get_duplicate_individuals(open_hds_cursor)
        rL.create_empty_kml(kml_file)
    elif disp == "houses_without_residency":
        data = genRep.houses_without_residency(open_hds_cursor)
        rL.create_kml_from_container(data, kml_file, "extId", "extId")
    else:
        rL.create_empty_kml(kml_file)
    return flask.render_template('issues.html', filename=filename)


@app.route('/archive')
@app.route('/archive/<path:path>')
@requires_auth
def archive(path=''):
    genRep.generate_reports(get_db('ODK_DB'), all_odk_forms, app.config['OPEN_HDS_DB'], get_db('OPEN_HDS_DB'),
                            period, int(app.config['MAX_REVISITS']), float(app.config['REVISIT_RADIUS']),
                            datetime.date.today(), APP_ROOT, app.config['SITE'])
    return ai.render_autoindex(path, endpoint='archive', template="archive.html")


def connect_to_database(which_db):
    return MySQLdb.connect(host=app.config['DB_HOST'], user=app.config['DB_USER'], passwd=app.config['DB_PW'],
                           db=app.config[which_db], cursorclass=MySQLdb.cursors.DictCursor)


def get_db(which_db):
    db = getattr(flask.g, which_db, None)
    if db is None:
        db = flask.g.which_db = connect_to_database(which_db)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(flask.g, 'ODK_DB', None)
    if db is not None:
        db.close()
    db = getattr(flask.g, 'OPENHDS_DB', None)
    if db is not None:
        db.close()


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000, passthrough_errors=True)
