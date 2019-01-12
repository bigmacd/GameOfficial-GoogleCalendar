import os
import mechanize
import cookielib
from bs4 import BeautifulSoup
import html2text
import time
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from gCalendar import gCalendar

def checkCalendar(mechBrowser, url, currentMonth):
    
    r = mechBrowser.open(url).read()
    soup = BeautifulSoup(r, 'html.parser')
    calendarEvent = None
    cancelled = None
    games = []

    x = soup.find_all("tr", {"class": "PaddingL5 PaddingR5 Font8"})
    for row in x:
        calendarEvent = None
        calendarEvent = row.input.a
        cols = row.find_all("td")
        for col in cols:
            if col.span is not None:
                if col.span.text == "Cancelled":
                    print ("found cancelled game");
                    calendarEvent = None
                    break
        if calendarEvent is not None:
            games.append(calendarEvent)
            
    #games = soup.find_all("a", { "label": "Create a vCalendar appointment for use in Outlook, Palm Desktop, etc." })
    if len(games) == 0:
        print ("No games found for {0}".format(currentMonth))
    gc = gCalendar()
    for game in games:
        #print (game['href'])
        g = BeautifulSoup(mechBrowser.open(game['href']).read(), 'html.parser')
        gc.addEvent(g.contents[0])


def main():
    if not os.environ.has_key('goUsername') or not os.environ.has_key("goPassword"):
        print ("cannot find Game Officials credentials")
        exit()

    # Browser
    br = mechanize.Browser()

    # Cookie Jar
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)

    # Browser options
    br.set_handle_equiv(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

    br.addheaders = [('User-agent', 'Chrome')]

    # The site we will navigate into, handling it's session
    br.open('https://www.gameofficials.net/public/default.cfm')

    # Select the second (index one) form (the first form is a search query box)
    br.select_form(nr=0)

    # User credentials
    br.form['username'] = os.environ['goUsername']
    br.form['password'] = os.environ['goPassword']

    # Login
    br.submit()

    # check this month
    url = "https://www.gameofficials.net/Game/myGames.cfm?viewRange=ThisMonth&module=myGames"
    print ("checking this month...")
    checkCalendar(br, url, "this month")

    # and next month
    today = datetime.date.today()
    p1month = relativedelta(months=1)
    today += p1month
    nextMonth = today.month
    nextMonthStr = today.strftime("%B")
    nextYear = today.year  # uh, why are we reffing in December?
    print ("Now checking {0}".format(nextMonthStr))
    url = "https://www.gameofficials.net/Game/myGames.cfm?module=myGames&viewRange=NextMonth&strDay={0}/1/{1}".format(nextMonth, nextYear)
    checkCalendar(br, url, nextMonthStr)

if __name__ == "__main__":
    while(True):
        today = datetime.datetime.now()
        try:
            main()
        except:
            pass

        h1 = today + timedelta(hours=1)
        print("Will check again at {:%H:%M:%S}".format(h1))
        time.sleep(60*60*1) # 1 hour