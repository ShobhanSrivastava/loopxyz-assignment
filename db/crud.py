import sqlite3
from sqlite3 import Connection

import os.path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'loop.db')
print(db_path)

def createConnection():
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return conn

def closeConnection(conn: Connection):
    conn.close()

def getDistinctStoreIDs(conn):
    result = conn.execute('select distinct store_id from store_status').fetchall()
    # print(type(result[0][0]))

    return result

def getStatusListForStoreID(conn, store_id):
    result = conn.execute(f'select status, timestamp_utc from store_status where store_id={store_id} order by timestamp_utc desc').fetchall()
    # print(result)

    return result

def getMenuHoursForStoreID(conn, store_id):
    result = conn.execute(f'select day, start_time_local, end_time_local from menu_hours where store_id={store_id}').fetchall()
    # print(result)

    return result

def getTimezoneForStoreID(conn, store_id):
    result = conn.execute(f'select timezone_str from timezones where store_id={store_id}').fetchone()
    # print(result[0])

    return result

def addStatusForReport(conn, report_id, status):
    conn.execute('insert into reports values(?, ?)', (report_id, status))
    conn.commit()

def updateStatusForReport(conn, report_id, status):
    conn.execute('update reports set status=? where report_id=?', (status, report_id))
    conn.commit()

def getStatusForReport(conn, report_id):
    result = conn.execute(f'select status from reports where report_id={report_id}').fetchone()
    return result

# addStatusForReport(2, "in-progress")
# updateStatusForReport(2, 'successful')
# getStatusForReport(2)
# getDistinctStoreIDs()
# getStatusListForStoreID(5955337179846162144)
# getMenuHoursForStoreID(5955337179846162144)
# getTimezoneForStoreID(5955337179846162144)