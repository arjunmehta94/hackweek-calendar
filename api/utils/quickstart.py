from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime
from datetime import timedelta
from dateutil import parser
from pytz import timezone

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def parse_request(r):
    params = {}
    if 'emails' not in r:
        raise Exception("missing email")
    if 'tz' not in r:
        raise Exception("missing timezone")
    params['items'] = [{'id': email} for email in r.get('emails')]
    if 'date' not in r:
        date = datetime.datetime.now().date()
    else:
        date = parser.parse(r.get('date')).date()
    if 'start_time' not in r:
        start_time = datetime.datetime.now()
        end_time = start_time + timedelta(hours=1)
        start_time = start_time.time()
        end_time = end_time.time()
    else:
        start_time = parser.parse(r.get('start_time')).time()
        end_time = parser.parse(r.get('end_time')).time()
    tz = r.get('tz')
    params['timeMin'] = timezone(tz).localize(datetime.datetime.combine(date, start_time)).isoformat()
    params['timeMax'] = timezone(tz).localize(datetime.datetime.combine(date, end_time)).isoformat()
    return params

def find_free_time(result, duration=60):
    calendars = result['calendars']
    time_min = parser.parse(result['timeMin'])
    time_max = parser.parse(result['timeMax'])
    all_busy_times = reduce(lambda x, y: x + y, [calendars[x]["busy"] for x in calendars.keys()])
    busy_array = [[parser.parse(x['start']), parser.parse(x['end'])] for x in all_busy_times]
    busy_array = _collapse_overlapping_intervals(busy_array)
    last_end = busy_array[-1][-1] if busy_array else None
    start_interval, end_interval = time_min, time_max
    if not last_end:
        return [start_interval, start_interval + timedelta(minutes=duration)]
    for busy in busy_array:
        tmp_start, tmp_end = busy[0], busy[1]
        if tmp_start > start_interval and (start_interval + timedelta(minutes=duration)) <= tmp_start:
            return [start_interval, start_interval + timedelta(minutes=duration)]
        start_interval = tmp_end
        if tmp_end == last_end:
            if (start_interval + timedelta(minutes=duration)) <= end_interval:
                return [start_interval, start_interval + timedelta(minutes=duration)]
    return None


def _collapse_overlapping_intervals(intervals):
    sorted_by_lower_bound = sorted(intervals, key=lambda tup: tup[0])
    merged = []

    for higher in sorted_by_lower_bound:
        if not merged:
            merged.append(higher)
        else:
            lower = merged[-1]
            # test for intersection between lower and higher:
            # we know via sorting that lower[0] <= higher[0]
            if higher[0] <= lower[1]:
                upper_bound = max(lower[1], higher[1])
                merged[-1] = [lower[0], upper_bound]  # replace by merged interval
            else:
                merged.append(higher)
    return merged

def parse_duration(duration):
    if duration[-1].lower() == 'h':
        return int(duration[:-1]) * 60
    elif duration[-1].lower() == 'm':
        return int(duration[:-1])
