import calendar
import datetime
import time


def play_store_timestamp_to_unix_timestamp(google_play_timestamp):
    pieces = google_play_timestamp.split()
    day = int(pieces[0])
    month = list(calendar.month_abbr).index(pieces[1])
    year = int(pieces[2])
    dt = datetime.datetime(year=year, month=month, day=day)
    return time.mktime(dt.timetuple())
