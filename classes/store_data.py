from collections import defaultdict
from typing import List
from datetime import datetime, time, timedelta
from utility.menu_hours_utc import utcOffset
from utility.datetime_util import create_datetime, create_time

class StoreData:
    def __init__(self, store_id):
        self.store_id:str = store_id
        self.statusList: List = []
        self.menuHours = defaultdict(None)
        self.timezone = 'America/Chicago'

    def populateStatusList(self, statusList):
        for status in statusList:
            timestamp = status[1]
            storeStatusAtTimestamp = status[0]

            self.statusList.append((timestamp, storeStatusAtTimestamp))

    def populateMenuHours(self, menuHoursData):
        for menuHourData in menuHoursData:
            day = int(menuHourData[0])
            startTime = menuHourData[1]
            endTime = menuHourData[2]

            self.menuHours[day] = (startTime, endTime)

    def addTimezone(self, timezoneData):
        if timezoneData is not None:
            self.timezone = timezoneData[0]

    def calculateUptimesDownTimes(self, timenow: datetime) -> List[int]:
        # Max timestamp of observation
        maxDate:datetime = timenow
        # Min timestamp of observation
        minDate:datetime = timenow - timedelta(days=7)

        # Creating a grid of 8 * 24 to store the hourly status between 18 Jan and 25 Jan and mark them as -1, which signifies that the data is missing
        # The rows are the dates [0 is for 18 and 7 is for 25] and cols are the hours
        weekdata:List[List[int]] = [[-1 for i in range(24)] for j in range(8)]

        # Mark the hours on 18 Jan before the min timestamp as -2, which signifies that we don't have to consider it
        for hour in range(24):
            if hour < minDate.hour:
                weekdata[0][hour] = -2

        # Mark the hours on 25 Jan after the max timestamp as -2, which signifies that we don't have to consider it
        for hour in range(24):
            if hour > maxDate.hour:
                weekdata[0][hour] = -2

        # Keep the track of active, inactive and missing data count
        hourActiveCount:List[int] = [0 for i in range(24)] # Set to 0 initially
        hourInactiveCount:List[int] = [0 for i in range(24)] # Set to 0 initially
        missingDataCount: List[int] = [7 for i in range(24)] # Set to 7 initially as assumed that all 7 for a particular hour is missing

        # Iterate on all the status available
        for status_row in self.statusList:
            # Get data from status tuple (timestamp, status)
            timestamp:datetime = create_datetime(status_row[0])
            status:str = status_row[1]

            # If the timestamp is outside the observation extremes, ignore it and move to the next timestamp
            if timestamp < minDate and timestamp > maxDate:
                continue

            # Get the dayIndex and the hourIndex from the timestamp
            # Data for 18 Jan and at 14:00:00 will be stored in the 0th row and 14th column
            dayIndex:int = timestamp.day - 18
            hourIndex:int = timestamp.hour

            # If there are multiple stamps for a particular hour, we'll go with the latest stamp
            # Since the timestamps are in decreasing order, latest timestamps will used first
            # If we get the timestamp for an hour again, ignore it and go for next timestamp
            if weekdata[dayIndex][hourIndex] != -1:
                continue

            # If the status is active, mark the respective position in weekdata as 1 signifying active store
            if status == 'active':
                weekdata[dayIndex][hourIndex] = 1
                hourActiveCount[hourIndex] += 1
            # Otherwise if the status is active, mark the respective position in weekdata as 0 signifying inactive store
            else: 
                weekdata[dayIndex][hourIndex] = 0
                hourInactiveCount[hourIndex] += 1

            # Reduce the missingDataCount for the particular hour
            missingDataCount[hourIndex] -= 1

        # Now we have all the data, we just need to find the active and inactive hours, but the menu hours are in local time so we need to find the respective utc time for the timestamps

        # utcOverlap for the days
        # Since the overlap maybe twice during a utc day, therefore a list
        # 0 => Monday and 6 => Sunday
        utc_overlap = [list() for i in range(7)]
        for day in range(7):
            # setting the default menu hours for the day as entire day
            menu_hours = (time(00,00,00), time(23,59,59))

            # if menu hours for some day is provided, set it equal to menu_hours
            if self.menuHours.get(day) is not None:
                menu_hours = (create_time(self.menuHours[day][0]), create_time(self.menuHours[day][0]))

            # start time of menu hours
            start_time:time = menu_hours[0]
            # end time of menu hours
            end_time:time = menu_hours[1]

            # For the start and end time we need to find the day offset and the hour
            # utcOffset function converts the given local time into utc time and returns the tuple (dayOffset, hours)
            # dayOffset signifies the offset of utc date with local date and has values -1, 0 or 1.
            # -1, 0 and 1 signify previous, same and next date respectively
            # The hour tells the hour value in the utc timestamp after conversion from the local timestamp
            utc_start_offset:tuple[int, int] = utcOffset(start_time, self.timezone)
            utc_end_offset:tuple[int, int] = utcOffset(end_time, self.timezone)

            # If both end and start have same offset, it means that both are in the same utc date
            if utc_start_offset[0] == utc_end_offset[0]:
                # The (day + utc_start_offset[0] + 7)%7 makes sure the values lie between 0 and 6
                # (0(Monday) - 1(utcOffset) + 7)%7 = 6(Sunday)
                # Similarly (6(Sunday) + 1(utcOffset) + 7)%7 = 0(Monday)
                utc_overlap[(day + utc_start_offset[0] + 7)%7].append([utc_start_offset[1], utc_end_offset[1]])
            else: 
            # If both end and start have different offsets, it means [start -> end of the day] and [start of the next day -> end] are the two overlaps
                utc_overlap[((day + utc_start_offset[0] + 7)%7)].append([utc_start_offset[1], 23])
                utc_overlap[((day + utc_end_offset[0] + 7)%7)].append([0, utc_end_offset[1]])


        # Now we try to create the missing values
        # The logic is: 
        # For missing data for an hour, say 13, we will check the percentage of times, the store was active or inactive on other days of the week at 13:00 
        # - Considerations: 
        #  - If the store was active more than 50% of times, we will say it was active 
        #  - If there are more than 3 missing values, store is considered inactive

        for hour in range(24):
            # Initially considering the calculated status as 0 or inactive 
            status_calculated:int = 0

            if(missingDataCount[hour] > 3):
                pass
            else:
                # Number of active hours
                activeCount:int = hourActiveCount[hour]
                # Number of inactive hours
                inactiveCount:int = hourInactiveCount[hour]

                # Percentage of active hours
                active_percentage:float = 100 * (activeCount / (activeCount + inactiveCount))

                # Only when active percentage is greater than 50, we will say that the store was opened
                if active_percentage > 50:
                    status_calculated = 1

            for day in range(8):
                # Ignore the the hours not under observation
                if weekdata[day][hour] == -2:
                    continue

                # Fill the missing values with calculated status
                if weekdata[day][hour] == -1:
                    weekdata[day][hour] = status_calculated


        # uptime counters
        uptimeLastDay:int = 0
        uptimeLastWeek:int = 0

        # uptime counters
        downtimeLastDay:int = 0
        downtimeLastWeek:int = 0

        # Setting curr date as min date, as we are starting to check from the min date
        curr_date:datetime = minDate

        for day in range(8):
            # Find the week of the day
            weekday = curr_date.weekday()
            for hour in range(24):
                # Ignore the out of observation cells
                if weekdata[day][hour] == -2:
                    continue

                # Check for all the overlaps for this weekday
                for utc_overlap_data in utc_overlap[weekday]:
                    # If the hour was between menu hours
                    if hour >= utc_overlap_data[0] and hour <= utc_overlap_data[1]:
                        # If the store was active
                        if weekdata[day][hour] == 1:
                            uptimeLastWeek += 1

                            # On the 6th day that is 24th Jan, increase uptimeLastDay
                            if day == 6:
                                uptimeLastDay += 1

                        # If the store was inactive
                        if weekdata[day][hour] == 0:
                            downtimeLastWeek += 1

                            # On the 6th day that is 24th Jan, increase uptimeLastDay
                            if day == 6:
                                downtimeLastDay += 1
                        
                        # 
                        # Once the uptime counter is increased break out of the loop
                        break

                    if weekdata[day][hour] == 1 and hour >= utc_overlap_data[0] and hour <= utc_overlap_data[1]:
                        uptimeLastWeek += 1
                        # On the 6th day that is 24th Jan, increase uptimeLastDay
                        if day == 6:
                            uptimeLastDay += 1


            # Increase the curr date by 1 day to get the weekday of the next day
            curr_date += timedelta(1)

        uptimeLastHour:int = 60 if weekdata[maxDate.day-18][maxDate.hour] == 1 else 0
        downtimeLastHour:int = 60 - uptimeLastHour

        rowData = [self.store_id, uptimeLastHour, uptimeLastDay, uptimeLastWeek, downtimeLastHour, downtimeLastDay, downtimeLastWeek]
        # print(rowData)

        return rowData