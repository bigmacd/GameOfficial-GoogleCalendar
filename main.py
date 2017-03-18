##################################### Method 1
import os
import mechanize
import cookielib
from bs4 import BeautifulSoup
import html2text
import datetime
from dateutil.relativedelta import relativedelta

from gCalendar import gCalendar

def checkCalendar(mechBrowser, url):
    
    r = mechBrowser.open(url).read()
    soup = BeautifulSoup(r, 'html.parser')

    games = soup.find_all("a", { "label": "Create a vCalendar appointment for use in Outlook, Palm Desktop, etc." })

    gc = gCalendar()
    for game in games:
        g = BeautifulSoup(br.open(game['href']).read(), 'html.parser')
        gc.addEvent(g.contents[0])


if not os.environ.has_key('goUsername') or not os.environ.has_key("goPassword"):
    print ("cannot find go credentials")
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
checkCalendar(br, url)

# and next month
today = datetime.date.today()
p1month = relativedelta(months=1)
today += p1month
nextMonth = today.month
nextYear = today.year  # uh, why are we reffing in December?
url = "https://www.gameofficials.net/Game/myGames.cfm?module=myGames&viewRange=NextMonth&strDay={0}/1/{1}".format(nextMonth, nextYear)
checkCalendar(br, url)


