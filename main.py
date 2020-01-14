import os
import mechanicalsoup
import time
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from gCalendar import gCalendar
from refWebSites import GameOfficials, MySoccerLeague


def checkWebsites():
    # Browser
    br = mechanicalsoup.StatefulBrowser(soup_config={ 'features': 'lxml'})
    br.addheaders = [('User-agent', 'Chrome')]

    websites = []
    websites.append(GameOfficials(br))
    websites.append(MySoccerLeague(br))

    for website in websites:
        assignments = website.getAssignments()

        gc = gCalendar()
        for assignment in assignments:
            gc.addEvent(assignment)

def main():
    try:
        x = os.environ['goUsername']
        y = os.environ["goPassword"]
    except KeyError:
        print ("cannot find Game Officials credentials")
        exit()

    try:
        x = os.environ['mslUsername']
        y = os.environ["mslPassword"]
    except KeyError:
        print ("cannot find MySoccerLeague credentials")
        exit()

    checkWebsites()

if __name__ == "__main__":
    while(True):
        today = datetime.datetime.now()
        try:
            main()
        except Exception as ex:
            print("Exception!!!: {0}".format(ex))

        h1 = today + timedelta(hours=1)
        print("Will check again at {:%H:%M:%S}".format(h1))
        time.sleep(60*60*1) # 1 hour
