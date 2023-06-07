from datetime import datetime, time

def create_datetime(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f %Z')
    except:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S %Z')

def create_time(time_str: str) -> time:
    return datetime.strptime(time_str, '%H:%M:%S').time()