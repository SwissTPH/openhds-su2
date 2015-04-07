#!/usr/bin/env python

"""genericReports.py: Reports common to all openHDS-based HDSS sites."""

__email__ = "nicolas.maire@unibas.ch"
__status__ = "Alpha"

import os
from difflib import SequenceMatcher
from datetime import date, datetime
import csv
import operator
import xlwt
import reportLib as rL


def create_summary_excel_report(odk_cursor, odk_forms, today, period, output_dir):
    w_houses_visited = xlwt.Workbook()
    visit_form = odk_forms['visit']
    #Houses visited in the last week:
    rL.create_excel_report_from_query(odk_cursor, w_houses_visited.add_sheet('Houses_visited'),
                                      "SELECT {fw}, {location} FROM {name} WHERE ADDDATE({date}, INTERVAL {period} DAY)"
                                      ">=CURDATE() ORDER BY {fw}, {location} ASC".format(period=period, **visit_form),
                                      [visit_form["fw"], visit_form["location"]])
    #Number of Houses visited in the last week per fw:
    rL.create_excel_report_from_query(odk_cursor, w_houses_visited.add_sheet('Houses_visited_by_FW'),
                                      "SELECT {fw}, COUNT(*) AS HousesVisited FROM {name} WHERE ADDDATE({date}, "
                                      "INTERVAL {period} DAY)>=CURDATE() GROUP BY {fw} ORDER BY HousesVisited "
                                      "ASC".format(period=period, **visit_form),
                                      [visit_form["fw"], "HousesVisited"])
    #Number of Houses visited in the last week per Day:
    rL.create_excel_report_from_query(odk_cursor, w_houses_visited.add_sheet('Houses_visited_per_Day'),
                                      "SELECT COUNT(*) AS HousesVisitedPerDay, {date} FROM {name} WHERE ADDDATE({date},"
                                      " INTERVAL {period} DAY)>=CURDATE() GROUP BY {date} ORDER BY {date} "
                                      "ASC".format(period=period, **visit_form),
                                      [visit_form["date"], "HousesVisitedPerDay"])
    #Number of Houses visited in the last week per fw, per Day:
    rL.create_excel_report_from_query(odk_cursor, w_houses_visited.add_sheet('Houses_visited_by_FW_per_Day'),
                                      "SELECT {fw}, COUNT(*) AS HousesVisitedPerDay, {date} FROM {name} WHERE "
                                      "ADDDATE({date}, INTERVAL {period} DAY)>=CURDATE() GROUP BY {fw}, {date} "
                                      "ORDER BY {fw}, {date} ASC".format(period=period, **visit_form),
                                      [visit_form["date"], visit_form["fw"], "HousesVisitedPerDay"])

    #Number of Forms filled in the last week per fw, per Day:
    for key, form in odk_forms.iteritems():
        if key == "visit" or key == "reVisit" or key == "reVisitEvents":
            continue
        rL.create_excel_report_from_query(odk_cursor, w_houses_visited.add_sheet(key),
                                          "SELECT COUNT(*) AS Nb, {fw}, {date} FROM {name} WHERE ADDDATE({date}, "
                                          "INTERVAL {period} DAY)>=CURDATE() GROUP BY {fw}, {date} ORDER BY {fw} "
                                          "ASC".format(period=period, **form), ["Nb", form["fw"], form["date"]])
    w_houses_visited.save(os.path.join(output_dir, "FieldProgressReport" + today.strftime("%Y-%m-%d") + ".xls"))


def get_missing_in_migrations(odk_cursor, odk_forms):
    missing_in_migrations = rL.query_db_all(odk_cursor, 'SELECT {migrationOut[fw]}, '
                                                        '{migrationOut[individual]}, '
                                                        '{migrationOut[location]}, {migrationOut[reason]}, '
                                                        '{migrationOut[is_internal]} FROM {migrationOut[name]} '
                                                        'WHERE {migrationOut[is_internal]}=\'YES\' AND '
                                                        '{migrationOut[name]}.{migrationOut[individual]} NOT IN '
                                                        '(SELECT {migrationIn[name]}.{migrationIn[individual]} '
                                                        'FROM {migrationIn[name]} WHERE {migrationIn[migration_type]}='
                                                        '\'INTERNAL_INMIGRATION\') '
                                                        'ORDER BY 1, 5 DESC'.format(**odk_forms))
    return missing_in_migrations


def get_nr_events_reported(odk_cursor, odk_forms):
    no_events_reported = rL.query_db_all(odk_cursor,
                                         'SELECT  "No Events" Event_Reported, {reVisit[name]}.{reVisit[location]}, '
                                         '{death[name]}.{death[individual]} DEATH, '
                                         '{migrationIn[name]}.{migrationIn[individual]} MIGRATIONIN, '
                                         '{migrationOut[name]}.{migrationOut[individual]} MIGRATIONOUT, '
                                         '{pregnancyOutcome[name]}.{pregnancyOutcome[individual]} PRGNOUTCOME, '
                                         '{pregnancyObservation[name]}.{pregnancyObservation[individual]} '
                                         'PREGOBSERVATION FROM ((((({reVisitEvents[name]} {reVisitEvents[name]} '
                                         'INNER JOIN {reVisit[name]} {reVisit[name]} '
                                         'ON ({reVisitEvents[name]}._TOP_LEVEL_AURI = '
                                         '{reVisit[name]}._URI)) LEFT OUTER JOIN {death[name]} {death[name]} '
                                         'ON ({death[location]} = '
                                         '{reVisit[name]}.{reVisit[location]})) LEFT OUTER JOIN '
                                         '{migrationIn[name]} {migrationIn[name]} '
                                         'ON ({migrationIn[location]} = '
                                         '{reVisit[name]}.{reVisit[location]})) LEFT OUTER JOIN '
                                         '{migrationOut[name]} {migrationOut[name]} '
                                         'ON ({migrationOut[location]} = '
                                         '{reVisit[name]}.{reVisit[location]})) LEFT OUTER JOIN '
                                         '{pregnancyObservation[name]} {pregnancyObservation[name]} '
                                         'ON ({pregnancyObservation[location]} = '
                                         '{reVisit[name]}.{reVisit[location]})) LEFT OUTER JOIN '
                                         '{pregnancyOutcome[name]} {pregnancyOutcome[name]} ON '
                                         '({pregnancyOutcome[location]} = '
                                         '{reVisit[name]}.{reVisit[location]}) WHERE '
                                         '{reVisitEvents[name]}.{reVisitEvents[fw]}=99 '
                                         'ORDER BY 1 DESC'.format(**odk_forms))
    return no_events_reported


def get_events_reported(odk_cursor, odk_forms):
    events_reported = rL.query_db_all(odk_cursor,
                                      'SELECT "DEATH" EVENT_REPORTED, '
                                      '{reVisit[name]}.{reVisit[location]}, '
                                      '{death[name]}.{death[individual]} FROM ({reVisitEvents[name]} '
                                      '{reVisitEvents[name]} INNER JOIN {reVisit[name]} '
                                      '{reVisit[name]} ON ({reVisitEvents[name]}._TOP_LEVEL_AURI = '
                                      '{reVisit[name]}._URI)) LEFT OUTER JOIN '
                                      '{death[name]} {death[name]} ON ({death[location]} = '
                                      '{reVisit[name]}.{reVisit[location]}) '
                                      'WHERE  {reVisitEvents[name]}.{reVisitEvents[fw]}=5 UNION SELECT '
                                      '\'OUT MIGRATION\', {reVisit[name]}.{reVisit[location]}, '
                                      '{migrationOut[name]}.{migrationOut[individual]} '
                                      'FROM ({reVisitEvents[name]} {reVisitEvents[name]} '
                                      'INNER JOIN {reVisit[name]} {reVisit[name]} ON '
                                      '({reVisitEvents[name]}._TOP_LEVEL_AURI='
                                      '{reVisit[name]}._URI)) LEFT OUTER JOIN '
                                      '{migrationOut[name]} {migrationOut[name]} ON '
                                      '({migrationOut[location]} = {reVisit[name]}.{reVisit[location]}) WHERE '
                                      '{reVisitEvents[name]}.{reVisitEvents[fw]}=1 '
                                      'UNION SELECT \'IN MIGRATION\', {reVisit[name]}.{reVisit[location]}, '
                                      '{migrationIn[name]}.{migrationIn[individual]} '
                                      'FROM ({reVisitEvents[name]} {reVisitEvents[name]} '
                                      'INNER JOIN {reVisit[name]} {reVisit[name]} ON '
                                      '({reVisitEvents[name]}._TOP_LEVEL_AURI ={reVisit[name]}._URI)) LEFT OUTER JOIN '
                                      '{migrationIn[name]} {migrationIn[name]} '
                                      'ON ({migrationIn[location]} = {reVisit[name]}.{reVisit[location]}) WHERE '
                                      '{reVisitEvents[name]}.{reVisitEvents[fw]}=2 UNION SELECT '
                                      '\'PREGNANCY OUTCOME\', {reVisit[name]}.{reVisit[location]}, '
                                      '{pregnancyOutcome[name]}.{pregnancyOutcome[individual]} FROM '
                                      '({reVisitEvents[name]} {reVisitEvents[name]} '
                                      'INNER JOIN {reVisit[name]} {reVisit[name]} ON '
                                      '({reVisitEvents[name]}._TOP_LEVEL_AURI ='
                                      ' {reVisit[name]}._URI)) LEFT OUTER JOIN '
                                      '{pregnancyOutcome[name]} {pregnancyOutcome[name]} ON '
                                      '({pregnancyOutcome[location]} = {reVisit[name]}.{reVisit[location]}) WHERE '
                                      '{reVisitEvents[name]}.{reVisitEvents[fw]}=4 UNION '
                                      'SELECT \'PREGNANCY OBSERVATION\', {reVisit[name]}.{reVisit[location]}, '
                                      '{pregnancyObservation[name]}.{pregnancyObservation[individual]} '
                                      'FROM ({reVisitEvents[name]} {reVisitEvents[name]} '
                                      'INNER JOIN {reVisit[name]} {reVisit[name]} ON '
                                      '({reVisitEvents[name]}._TOP_LEVEL_AURI = {reVisit[name]}._URI)) LEFT OUTER JOIN '
                                      '{pregnancyObservation[name]} {pregnancyObservation[name]} ON '
                                      '({pregnancyObservation[location]} = {reVisit[name]}.{reVisit[location]}) WHERE '
                                      '{reVisitEvents[name]}.{reVisitEvents[fw]}=3 '
                                      'ORDER BY 1 DESC'.format(**odk_forms))
    return events_reported


def create_problem_report(odk_cursor, odk_forms, open_hds_cursor, today, output_dir):
    visit_form = odk_forms['visit']
    w_problems = xlwt.Workbook()
    houses_without_visit_form = houses_without_visit_forms(odk_cursor, odk_forms, open_hds_cursor)
    rL.create_excel_report_from_container(w_problems.add_sheet("Houses without visit form"),
                                          ["House ID", "latitude", "longitude", "Date(s)", "FW(s)", "Event type(s)"],
                                          houses_without_visit_form)
    try:
        nr_events_reported = get_nr_events_reported(odk_cursor, odk_forms)
        rL.create_excel_report_from_container(w_problems.add_sheet("No events reported"),
                                              ["Event_Reported", "HOUSE_ID", "DEATH", "MIGRATIONIN", "MIGRATIONOUT",
                                               "PRGNOUTCOME", "PREGOBSERVATION"], nr_events_reported)
    except Exception as detail:
        print ("nr_events_reported failed: " + str(detail))

    try:
        events_reported = get_events_reported(odk_cursor, odk_forms)
        rL.create_excel_report_from_container(w_problems.add_sheet("Events reported"),
                                              ["EVENT_REPORTED", "HOUSE_ID", "PERMANENT_ID"], events_reported)
    except Exception as detail:
        print ("events_reported failed: " + str(detail))

    multi_out_migrations = get_multiple_out_migrations(odk_cursor, odk_forms)
    rL.create_excel_report_from_container(w_problems.add_sheet("Duplicate outmigrations"),
                                          ["Nb", odk_forms["migrationOut"]["individual"]], multi_out_migrations)
    multiple_in_migrations = get_multiple_in_migrations(odk_cursor, odk_forms)
    rL.create_excel_report_from_container(w_problems.add_sheet("Duplicate inmigrations"),
                                          ["Nb", odk_forms["migrationIn"]["individual"]], multiple_in_migrations)

    try:
        missing_in_migrations = get_missing_in_migrations(odk_cursor, odk_forms)
        rL.create_excel_report_from_container(w_problems.add_sheet("Missing internal migrations"),
                                              [odk_forms["migrationOut"]["fw"], odk_forms["migrationOut"]["individual"],
                                               odk_forms["migrationOut"]["location"],
                                               odk_forms["migrationOut"]["reason"],
                                               odk_forms["migrationOut"]["is_internal"]], missing_in_migrations)
    except Exception as detail:
        print ("missing_in_migrations failed: " + str(detail))

    multiple_visits = get_multiple_visits(odk_cursor, odk_forms)
    rL.create_excel_report_from_container(w_problems.add_sheet("Duplicate visits"), ["Nb", visit_form["location"]],
                                          multiple_visits)
    duplicate_individuals = get_duplicate_individuals(open_hds_cursor)
    rL.create_excel_report_from_container(w_problems.add_sheet("Duplicate individuals"),
                                          ["firstName", "middleName", "lastName", "extId", "dob", "collectedBy_uuid",
                                           "insertDate", "endDate", "extID", "latitude", "longitude"],
                                          duplicate_individuals)
    rL.create_kml_from_container(duplicate_individuals,
                                 os.path.join(output_dir, "DuplicateIndividuals.kml"), "id", "firstName")
    houses_wo_res = houses_without_residency(open_hds_cursor)
    rL.create_excel_report_from_container(w_problems.add_sheet('Houses without residency'),
                                          ["extId", "latitude", "longitude"], houses_wo_res)
    rL.create_kml_from_container(houses_wo_res, os.path.join(output_dir, "HousesWithoutResidency" +
                                                                         today.strftime("%Y-%m-%d") +
                                                                         ".kml"), "extId", "extId")
    w_problems.save(os.path.join(output_dir, "ProblemReport" + today.strftime("%Y-%m-%d") + ".xls"))


def create_overview_report(open_hds_cursor, today, output_dir):
    w_overview = xlwt.Workbook()
    records = rL.query_db_all(open_hds_cursor, 'SELECT individual.extId, individual.firstName, individual.middleName, '
                                               'individual.lastName, individual.gender, individual.dob, '
                                               'socialgroup.extId socialgroup, location.extId location, '
                                               'location.latitude, location.longitude, location.altitude, '
                                               'location.accuracy, membership.bIsToA FROM '
                                               '(((membership membership INNER JOIN individual '
                                               'individual ON (membership.individual_uuid = individual.uuid)) '
                                               'INNER JOIN socialgroup socialgroup ON '
                                               '(membership.socialGroup_uuid = socialgroup.uuid)) '
                                               'INNER JOIN residency residency ON '
                                               '(residency.individual_uuid = individual.uuid)) INNER JOIN '
                                               'location location ON (residency.location_uuid = location.uuid) '
                                               'WHERE membership.endDate IS NULL AND residency.endDate IS NULL and membership.deleted=0 '
                                               'ORDER BY socialgroup.extId, bIsToA')
    rL.create_excel_report_from_container(w_overview.add_sheet('Overview'),
                                          ['extId', 'firstName', 'middleName', 'lastName', 'gender', 'dob',
                                           'socialgroup', 'location', 'latitude', 'longitude', 'altitude',
                                           'accuracy', 'bIsToA'], records)
    w_overview.save(os.path.join(output_dir, "Overview" + today.strftime("%Y-%m-%d") + ".xls"))


def create_similar_individuals_report(open_hds_cursor, today, output_dir, threshold, ext_id_inclusion_list=None):
    w_fuzzy_dupes = xlwt.Workbook()
    #Find duplicated individuals by names, parent, dob
    individuals = rL.query_db_all(open_hds_cursor, "SELECT CONCAT(dob, firstName, lastName, middleName, "
                                                   "father_uuid, mother_uuid) AS id, uuid, extId FROM individual "
                                                   "WHERE uuid NOT LIKE 'Unknown Individual' "
                                                   "ORDER BY RAND() LIMIT 20")
    ind_list = []
    for i, individual1 in enumerate(individuals):
        if ext_id_inclusion_list and individual1["extId"] not in ext_id_inclusion_list:
            continue
        individual1_id = individual1["id"]
        for individual2 in individuals[i + 1:]:
            individual2_id = individual2["id"]
            similarity = SequenceMatcher(None, individual1_id, individual2_id).ratio()
            if similarity > threshold and not individual1["uuid"] == individual2["uuid"]:
                ind_list.append([individual1["uuid"], individual2["uuid"], similarity])
    duplicate_list = []
    for pair in ind_list:
        first = rL.query_db_one(open_hds_cursor, "SELECT firstName, middleName, lastName, i.extId, dob, "
                                                 "i.collectedBy_uuid, i.insertDate, r.endDate, l.extID, l.latitude, "
                                                 "l.longitude, CONCAT(firstName, '_', lastName, '_', "
                                                 "middleName, '_', dob) AS id, i.uuid "
                                                 "FROM individual i, residency r , location l "
                                                 "WHERE r.individual_uuid =i.uuid AND l.uuid=r.location_uuid AND "
                                                 "i.uuid='{uuid}' ORDER BY i.lastName, i.dob ".format(uuid=pair[0]))
        second = rL.query_db_one(open_hds_cursor, "SELECT firstName, middleName, lastName, i.extId, dob, "
                                                  "i.collectedBy_uuid, i.insertDate, r.endDate, l.extID, l.latitude, "
                                                  "l.longitude, CONCAT(firstName, '_', lastName, '_', "
                                                  "middleName, '_', dob) AS id, i.uuid "
                                                  "FROM individual i, residency r , location l "
                                                  "WHERE r.individual_uuid =i.uuid AND l.uuid=r.location_uuid AND "
                                                  "i.uuid='{uuid}' ORDER BY i.lastName, i.dob ".format(uuid=pair[1]))
        duplicate_list.append([first["id"], first["uuid"], first["extId"], second["id"], second["uuid"],
                               second["extId"], pair[2]])
    rL.create_excel_report_from_container(w_fuzzy_dupes.add_sheet("Similar individuals"),
                                          ["ID1", "uuid1", "extId1", "ID2", "uuid2", "extId2", "similarity"],
                                          duplicate_list)
    w_fuzzy_dupes.save(os.path.join(output_dir, "SimilarIndividuals" + today.strftime("%Y-%m-%d") + ".xls"))


def write_worksheet_record(worksheet, row_index, record):
    col_index = 0
    for cell in record:
        worksheet.write(row_index, col_index, cell)
        col_index += 1
    return row_index + 1


def get_individuals_where(cursor, select_clause, where_clause, group_clause):
    cursor.execute("SELECT {select_clause} FROM (((membership membership INNER JOIN individual individual ON "
                   "(membership.individual_uuid = individual.uuid)) INNER JOIN socialgroup socialgroup ON "
                   "(membership.socialGroup_uuid = socialgroup.uuid)) INNER JOIN residency residency ON "
                   "(residency.individual_uuid = individual.uuid)) INNER JOIN location location ON "
                   "(residency.location_uuid = location.uuid) WHERE {where_clause} {group_clause} ORDER BY "
                   "socialgroup.extId, bIsToA".format(select_clause=select_clause,
                                                      where_clause=where_clause, group_clause=group_clause))
    results = cursor.fetchall()
    return results


def calculate_person_years(cursor, to_date=None):
    if to_date is None:
        to_date = date.today()
    else:
        to_date = datetime.strptime(to_date, "%Y-%m-%d").date()
    cursor.execute("SELECT insertDate, endDate from residency")
    total_person_days = 0
    for row in cursor.fetchall():
        end_date = row["endDate"]
        insert_date = row["insertDate"]
        if end_date is None:
            person_days = (to_date - insert_date).days
        else:
            person_days = (to_date - insert_date).days
        total_person_days += person_days
    return total_person_days / 365.0


def get_individuals_data(cursor, where_clause, group_clause):
    return get_individuals_where(cursor, "individual.extId, individual.firstName, individual.middleName, "
                                         "individual.lastName,individual.gender, individual.dob, socialgroup.extId "
                                         "socialgroup, location.extId location,location.latitude, location.longitude, "
                                         "location.altitude, location.accuracy,  membership.bIsToA",
                                 where_clause, group_clause)


def houses_with_residency(open_hds_cursor):
    return rL.query_db_all(open_hds_cursor, 'SELECT extId, latitude, longitude FROM location WHERE uuid IN '
                                            '(SELECT location_uuid FROM residency WHERE endDate IS NULL)')


def houses_without_residency(open_hds_cursor):
    return rL.query_db_all(open_hds_cursor, 'SELECT extId, latitude, longitude FROM location WHERE uuid NOT IN '
                                            '(SELECT location_uuid FROM residency WHERE endDate IS NULL)')


def get_all_visits(odk_cursor, odk_forms, open_hds_cursor):
    visit_form = odk_forms['visit']
    houses_visited = {}
    visits = rL.query_db_all(odk_cursor, "SELECT DISTINCT {location}, {fw}, {date} FROM {name}".format(**visit_form))
    for visit in visits:
        location = visit[visit_form['location']]
        if not location in houses_visited:
            houses_visited[location] = {'visits': [], 'latitude': 0, 'longitude': 0}
        houses_visited[location]['visits'].append(visit)
    for form in odk_forms.values():
        if not 'location' in form.keys():
            continue
        form_records = rL.query_db_all(odk_cursor, "SELECT {location}, {fw}, {date} FROM {name}".format(**form))
        for record in form_records:
            event_type = form['name']
            location = record[form['location']]
            if not location in houses_visited:
                houses_visited[location] = {'events': [], 'latitude': 0, 'longitude': 0}
            else:
                if not 'events' in houses_visited[location]:
                    houses_visited[location]['events'] = []
            houses_visited[location]['events'].append([record[form['date']], event_type, record[form['fw']]])
    all_locations = '","'.join(houses_visited.keys())
    visited_coordinates = rL.query_db_all(open_hds_cursor, 'SELECT extId, latitude, longitude FROM location WHERE '
                                                           'extId IN ("{locations}")'.format(locations=all_locations))
    for coordinates in visited_coordinates:
        houses_visited[coordinates['extId']]['latitude'] = coordinates['latitude']
        houses_visited[coordinates['extId']]['longitude'] = coordinates['longitude']
    return houses_visited


def houses_without_visit_forms(odk_cursor, odk_forms, open_hds_cursor):
    visits = get_all_visits(odk_cursor, odk_forms, open_hds_cursor)
    no_visit_form = []
    for location in visits.keys():
        if not 'visits' in visits[location].keys():
            if not odk_forms['houseInfo']['name'] in [v[1] for v in visits[location]['events']]:
                fws = set([v[2] for v in visits[location]['events']])
                dates = set([v[0].strftime("%Y-%m-%d") for v in visits[location]['events']])
                event_types = set([v[1] for v in visits[location]['events']])
                latitude = visits[location]['latitude']
                longitude = visits[location]['longitude']
                no_visit_form.append({'House ID': location, 'latitude': latitude, 'longitude': longitude,
                                      'Date(s)': " | ".join(dates), 'FW(s)': " | ".join(fws),
                                      'Event type(s)': " | ".join(event_types)})
    return no_visit_form


def get_multiple_in_migrations(odk_cursor, odk_forms):
    in_migrations_by_ind = rL.query_db_all(odk_cursor, "SELECT COUNT(*) Nb, {individual} FROM {name} GROUP "
                                                       "BY {individual} ORDER BY "
                                                       "1 DESC".format(**odk_forms["migrationIn"]))
    return [rec for rec in in_migrations_by_ind if rec["Nb"] > 1]


def get_multiple_out_migrations(odk_cursor, odk_forms):
    out_migrations_by_ind = rL.query_db_all(odk_cursor, "SELECT COUNT(*) Nb, {individual} FROM {name} GROUP "
                                                        "BY {individual} ORDER BY "
                                                        "1 DESC".format(**odk_forms["migrationOut"]))
    return [rec for rec in out_migrations_by_ind if rec["Nb"] > 1]


def get_multiple_visits(odk_cursor, odk_forms):
    visit_form_by_house = rL.query_db_all(odk_cursor, "SELECT COUNT(*) Nb, {location}  FROM {name} GROUP BY "
                                                      "{location} ORDER BY 1 DESC".format(**odk_forms['visit']))
    return [rec for rec in visit_form_by_house if rec["Nb"] > 1]


def get_duplicate_individuals(open_hds_cursor):
    #Find duplicated individuals by names, parent, dob
    individual_count = rL.query_db_all(open_hds_cursor, "SELECT COUNT(CONCAT(dob, firstName, lastName, "
                                                        "father_uuid, mother_uuid)) AS Nb, dob, firstName, "
                                                        "lastName , middleName , father_uuid , mother_uuid FROM "
                                                        "individual GROUP BY CONCAT(dob, firstName, lastName, "
                                                        "father_uuid, mother_uuid)")
    duplicate_individuals = [rec for rec in individual_count if rec["Nb"] > 1]
    duplicate_individual_attributes = []
    for ind in duplicate_individuals:
        recs = rL.query_db_all(open_hds_cursor, "SELECT firstName, middleName, lastName, i.extId, dob, "
                                                "i.collectedBy_uuid, i.insertDate, r.endDate, l.extID, l.latitude, "
                                                "l.longitude, CONCAT(firstName, '.', lastName, '.', "
                                                "middleName, '-', dob) AS id "
                                                "FROM individual i, residency r , location l "
                                                "WHERE r.individual_uuid =i.uuid AND l.uuid=r.location_uuid AND "
                                                "i.dob='{dob}' AND i.lastName='{lastName}' AND "
                                                "i.firstName='{firstName}' "
                                                "AND i.father_uuid='{father_uuid}' AND i.mother_uuid='{mother_uuid}' "
                                                "ORDER BY i.lastName, i.dob ".format(**ind))
        for rec in recs:
            duplicate_individual_attributes.append(rec)

    return duplicate_individual_attributes


def get_operations_summary(cursor, all_odk_forms, odk_event_forms, period):
    visit_form = all_odk_forms["visit"]
    visit_counts = rL.query_db_all(cursor, "SELECT {fw}, COUNT(*) AS HousesVisitedPerDay, {date} FROM {name} "
                                           "WHERE ADDDATE({date}, INTERVAL {period} DAY)>=CURDATE() GROUP BY {fw}, "
                                           "{date} ORDER BY {fw}, {date} ASC".format(period=period, **visit_form))
    fws = sorted(list(set([d[visit_form["fw"]] for d in visit_counts])))
    dates = sorted(list(set([d[visit_form["date"]] for d in visit_counts])))
    hbfbd = {'x': fws, 'name': 'Fieldworker', 'title': 'Recent visits', 'y_label': 'Last week\'s visits'}
    data = []
    for fw in fws:
        houses_per_day = [r["HousesVisitedPerDay"] for r in visit_counts if r[visit_form["fw"]] == fw]
        rec = {"drilldown": {"name": fw, "categories": dates, 'data': houses_per_day}}
        rec['y'] = sum(rec["drilldown"]["data"])
        rec['color'] = 'colors[0]'
        data.append(rec)
    hbfbd["data"] = data
    return hbfbd


def get_event_rate_summary_by_event(cursor, all_odk_forms, odk_event_forms):
    """Number of Forms filled since start of round per fw, per visit"""
    visit_form = all_odk_forms["visit"]
    events = {k: all_odk_forms[k] for k in odk_event_forms}
    fws = rL.query_db_all(cursor, "SELECT DISTINCT {fw} FROM {name}".format(**visit_form))
    fws = sorted([fw[visit_form["fw"]] for fw in fws])
    ebvbf = {'x': events.keys(), 'name': 'Event type', 'title': 'Events reported per visit',
             'y_label': 'Events per visits'}
    tmp = []
    for fw in fws:
        total_visits = rL.query_db_one(cursor, "SELECT COUNT(*) AS Nb FROM {name} WHERE "
                                               "{fw}='{fieldworker}'".format(fieldworker=fw, **visit_form))['Nb']
        forms_filled = []
        for event, form in events.iteritems():
            event_count = rL.query_db_one(cursor, "SELECT '{event}', COUNT(*)/{visits} AS Nb FROM {name} "
                                                  "WHERE {fw}='{fieldworker}'".format(fieldworker=fw, event=event,
                                                                                      visits=total_visits, **form))
            event_count['Nb'] = round(float(event_count['Nb']), 2)
            forms_filled.append(event_count)
        events_reported = [r["Nb"] for r in forms_filled]
        tmp.append([fw, events_reported])
    data = []
    for index, event in enumerate(events.keys()):
        event_rates = [round(float(e[1][index]), 2) for e in tmp]
        rec = {'drilldown': {'name': event, 'categories': fws, 'data': event_rates}}
        #prevent division by zero
        denom = max(len(rec['drilldown']['data']),1)
        rec['y'] = round(sum(rec['drilldown']['data'])/denom, 2)
        rec['color'] = 'colors[0]'
        data.append(rec)
    ebvbf["data"] = data
    return ebvbf


def get_event_rate_summary_by_fw(cursor, all_odk_forms, odk_event_forms):
    """Number of Forms filled since start of round per fw, per visit"""
    visit_form = all_odk_forms['visit']
    events = {k: all_odk_forms[k] for k in odk_event_forms}
    fws = rL.query_db_all(cursor, "SELECT DISTINCT {fw} FROM {name}".format(**visit_form))
    fws = sorted([fw[visit_form['fw']] for fw in fws])
    ebvbf = {'x': fws, 'name': 'Fieldworker', 'title': 'Events reported per visit by Fieldworker',
             'y_label': 'Events per visits'}
    data = []
    for fw in fws:
        total_visits = rL.query_db_one(cursor, "SELECT COUNT(*) AS Nb FROM {name} WHERE "
                                               "{fw}='{fieldworker}'".format(fieldworker=fw, **visit_form))['Nb']
        forms_filled = []
        for event, form in events.iteritems():
            event_count = rL.query_db_one(cursor, "SELECT '{event}', COUNT(*)/{visits} AS Nb FROM {name} "
                                                  "WHERE {fw}='{fieldworker}'".format(fieldworker=fw, event=event,
                                                                                      visits=total_visits, **form))
            event_count['Nb'] = round(float(event_count['Nb']), 2)
            forms_filled.append(event_count)
        events_reported = [r['Nb'] for r in forms_filled]
        rec = {'drilldown': {'name': fw, 'categories': events.keys(), 'data': events_reported}}
        rec['y'] = round(sum(rec['drilldown']['data']), 2)
        rec['color'] = 'colors[0]'
        data.append(rec)
    ebvbf['data'] = data
    return ebvbf


def create_fw_visit_path(odk_cursor, odk_forms, open_hds_db_name, today, period, output_dir):
    all_fws = rL.query_db_all(odk_cursor, "SELECT DISTINCT {fw} FROM {name}".format(**odk_forms["visit"]))
    visit_date = odk_forms["visit"]["date"]
    for fw in all_fws:
        fw_id = fw[odk_forms["visit"]["fw"]]
        locations_visited = rL.query_db_all(odk_cursor, "SELECT START, END, {fw}, TIME_TO_SEC(TIMEDIFF(END,START))/60"
                                                        " as MINUTES, {location}, {date}, {lat} latitude, "
                                                        "{lon} longitude FROM  {name}, {openhdsDBName}.location WHERE "
                                                        "extId={location} AND ADDDATE({date}, INTERVAL {period} DAY)"
                                                        ">=CURDATE() AND {fw}='{fwid}' ORDER BY "
                                                        "START".format(openhdsDBName=open_hds_db_name,
                                                                       fwid=fw_id, period=period, **odk_forms["visit"]))
        rL.create_kml_from_container(locations_visited, os.path.join(output_dir, "LocationsVisitedBy" + fw_id + "-" +
                                                                                 today.strftime("%Y-%m-%d") + ".kml"),
                                     visit_date, odk_forms["visit"]["location"], start="START", end="END")


def create_revisit_guide(odk_cursor, odk_forms, open_hds_cursor, today, period, n_revisits, radius, output_dir):
    locations_to_revisit = rL.query_db_all(odk_cursor, "SELECT {location} FROM {name} WHERE ADDDATE({date}, INTERVAL "
                                                       "{period} DAY)>=CURDATE() "
                                                       "ORDER BY RAND()".format(period=period, nRevisits=n_revisits,
                                                                                **odk_forms["visit"]))
    location_ids = "','".join(lid[odk_forms["visit"]["location"]] for lid in locations_to_revisit)
    all_locations = rL.query_db_all(open_hds_cursor, "SELECT  extId, latitude, longitude FROM location WHERE extId in "
                                                     "('" + location_ids + "')")
    if len(all_locations) > 0:
        #only create a revisit file if there are any recently visited locations
        data = [all_locations[0]]
        for loc in all_locations[1:]:
            if rL.get_distance(data[0]['latitude'], data[0]['longitude'], loc['latitude'], loc['longitude']) < radius:
                data.append(loc)
        data = data[0:n_revisits]
        outfile_path = os.path.join(output_dir, "LocationsToRevisit" + today.strftime("%Y-%m-%d") + ".kml")
        rL.create_kml_from_container(data, outfile_path, "extId", "extId")
        w_revisit = xlwt.Workbook()
        rL.create_excel_report_from_container(w_revisit.add_sheet('Houses to revisit'), ["extId", "latitude", "longitude"],
                                              data)
        w_revisit.save(os.path.join(output_dir, "LocationsToRevisit" + today.strftime("%Y-%m-%d") + ".xls"))


def create_all_generic_reports(odk_cursor, all_odk_forms, open_hds_cursor, open_hds_db_name, today, period, n_revisits,
                               radius, output_dir):
    create_operations_reports(odk_cursor, all_odk_forms, open_hds_cursor, open_hds_db_name, today, period, n_revisits,
                              radius, output_dir)
    create_overview_report(open_hds_cursor, today, output_dir)
    #create_similar_individuals_report(open_hds_cursor, today, output_dir, 0.95, ext_id_inclusion_list=None)


def create_operations_reports(odk_cursor, all_odk_forms, open_hds_cursor, open_hds_db_name, today, period, n_revisits,
                              radius, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    create_summary_excel_report(odk_cursor, all_odk_forms, today, period, output_dir)
    create_problem_report(odk_cursor, all_odk_forms, open_hds_cursor, today, output_dir)
    visit_path_dir = os.path.join(output_dir, "recentlyVisited")
    if not os.path.exists(visit_path_dir):
        os.makedirs(visit_path_dir)
    create_fw_visit_path(odk_cursor, all_odk_forms, open_hds_db_name, today, period, visit_path_dir)
    create_revisit_guide(odk_cursor, all_odk_forms, open_hds_cursor, today, period, n_revisits, radius, output_dir)


def houses_visited_with_missing_health_info_forms(odk_cursor, odk_forms, open_hds_db_name, houses_with_visit_form):
    visited_locations = "','".join(houses_with_visit_form)
    houses_with_missing_health_info = rL.query_db_all(odk_cursor,
                                                      "SELECT i.extId ID, l.extId location FROM "
                                                      "{openhdsDBName}.residency r, {openhdsDBName}.individual i, "
                                                      "{openhdsDBName}.location l WHERE l.uuid=r.location_uuid AND "
                                                      "i.uuid=r.individual_uuid AND r.endDate IS NULL AND "
                                                      "l.extId in ('{visited_locations}') AND "
                                                      "i.extId NOT IN (SELECT {individual} "
                                                      "FROM {name})".format(openhdsDBName=open_hds_db_name,
                                                                            visited_locations=visited_locations,
                                                                            **odk_forms['individualHealthInfo']))
    return houses_with_missing_health_info


def houses_with_missing_health_info_forms(odk_cursor, odk_forms, open_hds_db_name):
    houses_with_missing_health_info = rL.query_db_all(odk_cursor,
                                                      "SELECT DISTINCT l.extId House FROM "
                                                      "{openhdsDBName}.residency r, {openhdsDBName}.individual i, "
                                                      "{openhdsDBName}.location l WHERE l.uuid=r.location_uuid "
                                                      "and i.uuid=r.individual_uuid and r.endDate IS NULL AND "
                                                      "i.extId NOT IN (SELECT {individual} "
                                                      "FROM {name})".format(openhdsDBName=open_hds_db_name,
                                                                            **odk_forms['individualHealthInfo']))
    return houses_with_missing_health_info


def create_cluster_kml_files(odk_cursor, all_odk_forms, open_hds_db_name, today, root_dir, output_dir):
    incomplete_individual_health_info = houses_with_missing_health_info_forms(odk_cursor, all_odk_forms,
                                                                              open_hds_db_name)
    incomplete_individual_health_info = [d['House'] for d in incomplete_individual_health_info]
    w_excluded_from_kml = xlwt.Workbook()
    for mc_file_name in os.listdir(os.path.join(root_dir, "clusterLists")):
        if mc_file_name.startswith("MC") and mc_file_name.endswith(".txt"):
            assignment_file = open(os.path.join(root_dir, "clusterLists", mc_file_name), "rb")
            data = sorted(csv.DictReader(assignment_file, delimiter="\t"),
                          key=operator.itemgetter("Cluster", "House", "IndividualID"))
            #TODO: the next 2 lines fix the non-conforming names of locations (Houses) in the current cluster files
            for r in data:
                r["House"] = r["House"][0:3] + r["House"][3:].zfill(6)
            filtered_data = [rec for rec in data if (rec['House'] in incomplete_individual_health_info) or
                             (rec['IndividualID'].startswith('Abandonded house'))]
            outfile_path = os.path.join(output_dir, mc_file_name[:-4] + "-" + today.strftime("%Y-%m-%d") + ".kml")
            rL.create_kml_from_container(filtered_data, outfile_path, 'Cluster', 'Cluster')
            filtered_out = [rec for rec in data if not ((rec['House'] in incomplete_individual_health_info) or
                                                        (rec['IndividualID'].startswith('Abandonded house')))]
            rL.create_excel_report_from_container(w_excluded_from_kml.add_sheet(mc_file_name[:-4]),
                                                  ['IndividualID', 'Name', 'House',
                                                   'latitude', 'longitude'], filtered_out)
            w_excluded_from_kml.save(os.path.join(output_dir, "ExcludedFromVisitKMLs" + today.strftime("%Y-%m-%d")
                                                              + ".xls"))


def generate_reports(odk_conn, all_odk_forms, open_hds_db_name, open_hds_conn, period,
                     revisits, radius, today, root_dir, site):
    odk_cursor = odk_conn.cursor()
    open_hds_cursor = open_hds_conn.cursor()
    report_name = "reports" + site + today.strftime("%Y-%m-%d")
    report_path = os.path.join(root_dir, "static", "archive", report_name)
    filename = report_path+".zip"
    if not os.path.isfile(filename):
        create_all_generic_reports(odk_cursor, all_odk_forms, open_hds_cursor, open_hds_db_name, today, period,
                                   revisits, radius, report_path)
        if site == "Rusinga":
            cluster_kml_dir = os.path.join(report_path, "notYetVisited")
            if not os.path.exists(cluster_kml_dir):
                os.makedirs(cluster_kml_dir)
            create_cluster_kml_files(odk_cursor, all_odk_forms, open_hds_db_name, today, root_dir, cluster_kml_dir)
        rL.zip_folder(report_name, report_path)
    odk_conn.close()
    open_hds_conn.close()

