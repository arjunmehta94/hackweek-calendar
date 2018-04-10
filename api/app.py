#!flask/bin/python
from flask import Flask
from flask import request
from flask import jsonify
from utils.quickstart import get_credentials
import httplib2
from apiclient import discovery
import datetime

credentials = None

app = Flask(__name__)

@app.route('/')
def hello():
  return "hello"

@app.route('/events', methods=['GET'])
def index():
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
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
  print jsonify(request.json)
  return "hello"

if __name__ == '__main__':
  credentials = get_credentials()
  http = credentials.authorize(httplib2.Http())
  service = discovery.build('calendar', 'v3', http=http)
  app.run(debug=True)