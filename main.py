import os
import mechanicalsoup

#import html2text
import time
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from gCalendar import gCalendar

baseUrl = "https://www.gameofficials.net"

def checkCalendar(mechBrowser, url, currentMonth):
    
    gamePage = mechBrowser.get(url)
    calendarEvent = None
    cancelled = None
    games = []

    # get all the games...
    gameList = gamePage.soup.find_all("tr", { "class" : "PaddingL5 PaddingR5 Font8"})

    for row in gameList:
        cols = row.find_all("td")

        # look for cancelled
        try:
            cols[2].text.index("Cancelled")
            # yep, it's been cancelled
            continue
        except ValueError:
            pass
        
        # not cancelled, so get the url of the ical data
        aas = cols[0].find_all("a")
        # there should be two a tags
        if len(aas) != 2:
            print ("Row {0} seems broken!!!, there are {1} and there should be 2!!!!!"
                   .format(row.text, len(aas)))
            continue

        games.append(aas[1]['href'])
            
    if len(games) == 0:
        print ("No games found for {0}".format(currentMonth))
    else:
        gc = gCalendar()
        for game in games:
            #print (game['href'])
            icalPage = mechBrowser.get(baseUrl + game)
            gc.addEvent(icalPage.text)


def main():
    try:
        x = os.environ['goUsername']
        y = os.environ["goPassword"]
    except KeyError:
        print ("cannot find Game Officials credentials")
        exit()

    # Browser
    br = mechanicalsoup.Browser(soup_config={ 'features': 'lxml'})
    br.addheaders = [('User-agent', 'Chrome')]

    # The site we will navigate into, handling it's session
    login_page_url = baseUrl + '/public/default.cfm'
    login_page = br.get(login_page_url)
    login_page.raise_for_status()

    # Select the second (index one) form (the first form is a search query box)
    login_form = mechanicalsoup.Form(login_page.soup.select_one('form'))
    
    # User credentials
    login_form.input({ 'username': os.environ['goUsername'],
                       'password': os.environ['goPassword'] })

    # Login
    login_result = br.submit(login_form, login_page_url)

    # check this month
    url = baseUrl +  "/Game/myGames.cfm?viewRange=ThisMonth&module=myGames"
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
    url = baseUrl + "/Game/myGames.cfm?module=myGames&viewRange=NextMonth&strDay={0}/1/{1}".format(nextMonth, nextYear)
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