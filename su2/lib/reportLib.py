#!/usr/bin/env python

"""reportLib.py: Support for report generation from openHDS/ODK."""

__email__ = "nicolas.maire@unibas.ch"
__status__ = "Alpha"

import smtplib
import os
import shutil
import zipfile
import math

import datetime

from email import Encoders
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

import simplekml


def send_mail(send_from, send_to, subject, text, files=None, server="localhost"):
    if files is None:
        files = []
    assert type(send_to) == list
    assert type(files) == list

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(text))

    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(f, "rb").read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)

    smtp = smtplib.SMTP(server)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()


def zip_folder(name, path):
    zip_object = zipfile.ZipFile(path + '.zip', 'w', zipfile.ZIP_DEFLATED)
    root_length = len(path) + 1
    for base, dirs, files in os.walk(path):
        for f in files:
            fn = os.path.join(base, f)
            zip_object.write(fn, os.path.join(name, fn[root_length:]))
    shutil.rmtree(path)


def get_distance(lat1, lon1, lat2, lon2):
    lat1 = float(lat1)
    lon1 = float(lon1)
    lat2 = float(lat2)
    lon2 = float(lon2)
    R = 6373.0
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (math.sin(dlat/2))**2 + math.cos(lat1) * math.cos(lat2) * (math.sin(dlon/2))**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    return distance


def years_ago(years, from_date=None):
    if from_date is None:
        from_date = datetime.date.now()
    try:
        return from_date.replace(year=from_date.year - years)
    except:
        # Must be 2/29!
        assert from_date.month == 2 and from_date.day == 29
        return from_date.replace(month=2, day=28, year=from_date.year - years)


def query_db_all(db_cursor, query):
    db_cursor.execute(query)
    return db_cursor.fetchall()


def query_db_one(db_cursor, query):
    db_cursor.execute(query)
    return db_cursor.fetchone()


def create_excel_report_from_container(worksheet, fields, records):
    for colIndex, field in enumerate(fields):
        worksheet.write(0, colIndex, field)
    for rowIndex, record in enumerate(records):
        for colIndex, field in enumerate(fields):
            if type(record) == dict:
                cell = record[field]
            elif type(record) == list or type(record) == tuple:
                cell = record[colIndex]
            else:
                cell = record
            if type(cell) == datetime.datetime or type(cell) == datetime.date:
                cell = cell.strftime("%Y-%m-%d")
            worksheet.write(rowIndex + 1, colIndex, cell)


def create_excel_report_from_query(cursor, worksheet, query, fields):
    records = query_db_all(cursor, query)
    create_excel_report_from_container(worksheet, fields, records)


def create_kml_from_container(data, filename, color_separator, name, start="", end=""):
    icon_colors = ["ff0000ff", "ff00ff00", "ffff0000", "ff00ffff", "ffff00ff", "ffffff00",
                   "ff000077", "ff007700", "ff770000", "ff007777", "ff770077", "ff777700",
                   "ff7777ff", "ff77ff77", "ffff7777", "ff77ffff", "ffff77ff", "ffffff77",
                   "ff0077ff", "ff77ff00", "ffff0077"]
    icon_styles = []
    for color in icon_colors:
        shared_style = simplekml.Style()
        shared_style.iconstyle.color = color
        shared_style.labelstyle.scale = 0.5
        shared_style.iconstyle.scale = 0.5
        icon_styles.append(shared_style)

    kml = simplekml.Kml()
    color_index = 0
    previous_color_separator_id = ''
    for rec in data:
        color_separator_id = rec[color_separator]
        if color_separator_id != previous_color_separator_id:
            color_index += 1
            previous_color_separator_id = color_separator_id
        pnt = kml.newpoint(name=rec[name])
        pnt.coords = [(rec['longitude'], rec['latitude'])]
        pnt.style = icon_styles[color_index % len(icon_colors)]
        if start != "":
            if end != "":
                pnt.timespan.start = start
                pnt.timespan.end = end
            else:
                pnt.timestamp.when = start
        for key, value in rec.iteritems():
            key = str(key).replace('*', '').replace('<Null>', '')
            value = str(value).replace('*', '').replace('<Null>', '')
            pnt.extendeddata.newdata(name=key, value=value)
    kml.save(filename)


def create_empty_kml(filename):
    kml = simplekml.Kml()
    kml.save(filename)

