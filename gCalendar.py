from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime
import icalendar
import json

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentialsgameofficials.json
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'gameofficials'

class gCalendar:
    
    def __init__(self):
        try:
            import argparse
            self.flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        except ImportError:
            self.flags = None

        self.credentials = self.get_credentials()
        self.http = self.credentials.authorize(httplib2.Http())
        self.service = discovery.build('calendar', 'v3', http=self.http)


    def get_credentials(self):
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
                                       'gameofficials.json')

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.user_agent = APPLICATION_NAME
            if self.flags:
                credentials = tools.run_flow(flow, store, self.flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
        return credentials

    def addEvent(self, icsData, checkForExisting=False):
        event = self.icsToEvent(icsData)
        if not self.eventExists(event['description']):
            event = self.service.events().insert(calendarId='primary', body=event).execute()

    def eventExists(self, game):
        # parse 'game' for the game number, then see if we can find that already in the calendar
        gStart = game.find("[Game: ")
        gStart += len("[Game: ")
        gEnd = game.find(']')
        gEnd = len(game) - gEnd
        gId = game[gStart:-gEnd]
        searchString = '"[Game: {0}]"'.format(gId)
        # only start looking from the beginning of this month as game number from previous years recycle
        now = datetime.datetime.utcnow()
        now = now.replace(day=1)
        timemin = now.isoformat() + 'Z'
#        print ("game id: {0}".format(gId))
        events = self.service.events().list(calendarId='primary', timeMin=timemin, q=searchString).execute()
#        print ("game found? {0}".format(len(events['items']) > 0))
        return len(events['items']) > 0

    def icsToEvent(self, icsData):    
        calendar = icalendar.Calendar.from_ical(icsData)
        for entry in calendar.walk('VEVENT'):
            return { 'summary': entry['SUMMARY'],
                     'location': entry['LOCATION'],
                     'description': entry['DESCRIPTION'],
                     'start': { 'dateTime': entry['DTSTART'].dt.strftime('%Y-%m-%dT%H:%M:%S-00:00'),
                                'timeZone': "UTC"
                     },
                     'end': { 'dateTime': entry['DTEND'].dt.strftime('%Y-%m-%dT%H:%M:%S-00:00'),
                              'timeZone': "UTC"
                     }
            } 

