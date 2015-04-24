#!/usr/bin/env python

"""generateReports.py: Offline report generation"""

__email__ = "nicolas.maire@unibas.ch"
__status__ = "Alpha"

import argparse
import ConfigParser
import datetime
import os
import MySQLdb.cursors
import json

import genericReports as gR
import reportLib as rL


#Add fake header for config files: http://stackoverflow.com/questions/2819696/parsing-properties-file-in-python/2819788#2819788
class FakeSectionHead(object):
    def __init__(self, fp):
        self.fp = fp
        self.fake_head = '[general]\n'

    def readline(self):
        if self.fake_head:
            try:
                return self.fake_head
            finally:
                self.fake_head = None
        else:
            return self.fp.readline()


def get_cfv(cfg, key):
    return cfg.get('general', key).replace("'", "")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='cmdln arguments')
    parser.add_argument('-c', '--configFile', help='Configuration File', required=True)
    parser.add_argument('-m', '--mail', help='Send an email?', action="store_true")
    args = parser.parse_args()
    config = ConfigParser.RawConfigParser()
    with open(args.configFile) as cf:
        config.readfp(FakeSectionHead(cf))
    db_user = get_cfv(config, 'DB_USER')
    db_pw = get_cfv(config, 'DB_PW')
    db_host = get_cfv(config, 'DB_HOST')
    odk_db_name = get_cfv(config, 'ODK_DB')
    open_hds_db_name = get_cfv(config, 'OPEN_HDS_DB')
    odk_conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pw, db=odk_db_name,
                               cursorclass=MySQLdb.cursors.DictCursor)
    openhds_conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pw, db=open_hds_db_name,
                               cursorclass=MySQLdb.cursors.DictCursor)
    period = get_cfv(config, 'BACK_REPORT_DAYS')
    revisits = int(get_cfv(config, 'MAX_REVISITS'))
    radius = float(get_cfv(config, 'REVISIT_RADIUS'))
    site = get_cfv(config, 'SITE')
    today = datetime.date.today()

    with open(os.path.join('..', 'conf', get_cfv(config, 'FORM_DEFINITIONS')), 'rb') as fp:
        form_definitions = json.load(fp)
    all_odk_forms = form_definitions['all_forms']
    odk_event_forms = form_definitions['event_forms']
    gR.generate_reports(odk_conn, all_odk_forms, open_hds_db_name, openhds_conn, period,
                        revisits, radius, today, "..", site)
    if args.mail:
        rL.send_mail(config.get('mailConfig', 'sender'), config.get('mailConfig', 'recipients').split(","),
                     "HDSS reports, " + today.strftime("%Y/%m/%d"), config.get('mailConfig', 'mailBody'),
                     server=config.get('mailConfig', 'smtpServer'))
