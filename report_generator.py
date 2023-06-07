import csv
from db.crud import getDistinctStoreIDs, getMenuHoursForStoreID, getStatusListForStoreID, getTimezoneForStoreID, closeConnection
from classes.store_data import StoreData
from datetime import datetime


def generateReport(conn, timenow, report_id):
    timebefore = datetime.now()

    count = 0
    distinct_stores = getDistinctStoreIDs(conn)
    for store in distinct_stores:
        if count == 140:
            break

        count += 1

        # Get the store_id from the tuple
        store_id = store[0]

        # If it is the heading row, ignore it
        if store_id == 'store_id':
            continue

        currStore = StoreData(store_id)

        # Get the status list for this store and add it to the currStore statusList
        statusList = getStatusListForStoreID(conn, store_id)
        currStore.populateStatusList(statusList)

        # Get the menu_hours for the store and add it to the currStore menuHours
        menuHoursData = getMenuHoursForStoreID(conn, store_id)
        currStore.populateMenuHours(menuHoursData)

        # Get the store timezone and add it to the currStore timezone
        timezone = getTimezoneForStoreID(conn, store_id)
        currStore.addTimezone(timezone)

        output = []
        uptimeDowntimeData = currStore.calculateUptimesDownTimes(timenow)
        output.append(uptimeDowntimeData)
            
    writeToCSV(report_id, output)
    timeafter = datetime.now()

    print('Time Taken = ', (timeafter-timebefore).seconds)

def writeToCSV(report_id, outputList):
    with open(f'reports/{report_id}.csv', 'w') as file:
        csv_writer = csv.writer(file)

        # The first row of the csv report
        csv_writer.writerow(['store_id','uptime_last_hour(in minutes)','uptime_last_day(in hours)','uptime_last_week(in hours)','downtime_last_hour(in minutes)','downtime_last_day(in hours)','downtime_last_week(in hours)'])

        for output in outputList:
            csv_writer.writerow(output)

# timenow = create_datetime('2023-01-25 18:13:22.479220 UTC')
# generateReport(int(uuid.uuid1()), timenow)
# generateReport(timenow, 12345)





