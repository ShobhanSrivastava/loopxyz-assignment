from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

def utcOffset(localTime:time, timezone_str:str):
    # Initialising timezone with 'America/Chicago' as some timezones are not recognised by pytz so throws an error
    timezoneLocal = ZoneInfo('America/Chicago')
    try:
        # Try to create a timezone if it is a known timezone to pytz otherwise considering it as America/Chicago
        timezoneLocal = ZoneInfo(timezone_str)
    except:
        pass

    # Localising a timestamp to the store timezone
    localisedTimestamp = datetime(2023, 1, 18, localTime.hour, localTime.minute, localTime.second, tzinfo=timezoneLocal)


    # Converting the timestamp to utc timestamp
    utcTimestamp = localisedTimestamp.astimezone(timezone.utc)

    # Return the tuple (dayOffset, hour)
    return (utcTimestamp.day - localisedTimestamp.day, utcTimestamp.hour)

# print(utcOffset(time(6,30,00), 'Asia/Boise'))