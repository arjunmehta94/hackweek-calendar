#!flask/bin/python
from __future__ import print_function
from flask import Flask
from flask import abort
from flask import request
from flask import jsonify
from utils.quickstart import get_credentials
from utils.quickstart import parse_request
from utils.quickstart import find_free_time
import httplib2
from apiclient import discovery
import datetime


app = Flask(__name__)


@app.route('/')
def hello():
    return "hello"


@app.route('/events', methods=['GET'])
def index():
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC tim
    print('Getting the upcoming 10 events')
    eventsResult = calendarService.events().list(
        calendarId='primary', timeMin=now, maxResults=2, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])
    return jsonify(results=events)


@app.route('/calendar/create', methods=['POST'])
def create_event():
    duration = int(request.json.get('duration', '1'))
    params = parse_request(request.json)
    is_free_time = False
    resourceResult = resourceService.resources().calendars().list(
        customer='my_customer', orderBy='capacity').execute()
    resources = resourceResult.get('items', [])
    params['items'].append({'id': resources[0]['resourceEmail']})
    try:
        for resource in resources:
            params['items'].append({'id': resources[0]['resourceEmail']})
            result = calendarService.freebusy().query(body=params).execute()
            free_times = find_free_time(result, duration)
            if free_times:
                is_free_time = True
                break
            params['items'].pop()
    except Exception as error:
        abort(jsonify(message=str(error)))
    if not is_free_time:
        return "No free time"
    start_time, end_time = free_times[0].isoformat(), free_times[1].isoformat()
    attendees = [{"email": email['id']} for email in params['items']]
    event = calendarService.events().insert(calendarId='primary', body={
        'start': {
            'dateTime': start_time
        },
        'end': {
            'dateTime': end_time
        },
        'attendees': attendees
    }).execute()
    return jsonify(event)

if __name__ == '__main__':
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    calendarService = discovery.build('calendar', 'v3', http=http)
    resourceService = discovery.build('admin', 'directory_v1', http=http)
    app.run(debug=True)
