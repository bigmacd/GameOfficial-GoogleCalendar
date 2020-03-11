import os
import mechanicalsoup
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import uuid
import time
import pytz

class RefereeWebSite(object):

    def __init__(self, br):
        self._browser = br

    def baseUrl(self):
        return self._baseUrl

    def loginPage(self):
        return self._loginPage

    def loginFormInput(self):
        return self._loginFormInput


class MySoccerLeague(RefereeWebSite):

    def __init__(self, br):
        super(MySoccerLeague, self).__init__(br)
        self._baseUrl = self._loginPage = "https://mysoccerleague.com/YSLmobile.jsp"
        self._loginFormInput = { 'userName': os.environ['mslUsername'],
                                'password': os.environ['mslPassword'] }
        self._dataItems = ['card',
                           'datetime',
                           'league',
                           'gamenumber',
                           'field',
                           'agegroup',
                           'gender',
                           'level',
                           'hometeam',
                           'awayteam'
                           'ref'
                           'assistant1',
                           'assistant2' ]
        self._daylightSavingsTime = True
        if time.localtime().tm_isdst == 0:
            self._daylightSavingsTime = False
        self._tz = pytz.timezone('America/Detroit')

    def getAssignments(self):
        retVal = []
        try:
            # The site we will navigate into, handling it's session
            self._browser.open(self._baseUrl)
            #print(self._browser.get_current_page())

            #login_page.raise_for_status()
            self._browser.select_form('form')
            #self._browser.get_current_form().print_summary()
            self._browser['userName'] = self._loginFormInput['userName']
            self._browser['password'] = self._loginFormInput['password']
            response = self._browser.submit_selected()

            # MSL url for current assignments
            # need to extract the key fom the login_result first
            url = "https://mysoccerleague.com/{0}".format(response.soup.find_all('a')[13]['href'])
            assignments_page = self._browser.open(url)
            rowtype1 = assignments_page.soup.find_all("tr", { "class" : 'trstyle1'})
            rowtype2 = assignments_page.soup.find_all("tr", { "class" : 'trstyle2'})
            assignments = rowtype1 + rowtype2

            print("Found {0} assignments at {1}".format(len(assignments),
                                                        self._baseUrl))

            for a in assignments:
                elements = a.find_all('td')
                retVal.append(self._makeIcal(elements))

        except Exception as ex:
            print(ex)

        return retVal

    def _makeIcal(self, gameDetails):
        # Convert times (3 of them) to UTC
        dtstamp = datetime.datetime.now()
        localstamp = self._tz.localize(dtstamp, is_dst = self._daylightSavingsTime)
        utcstamp = localstamp.astimezone(pytz.utc)

        dtstart = datetime.datetime.strptime(gameDetails[1].text, "%m/%d/%Y - %I:%M %p")
        localstart = self._tz.localize(dtstart, is_dst = self._daylightSavingsTime)
        utcstart = localstart.astimezone(pytz.utc)

        dtend = dtstart + timedelta(minutes=40) # average 40 minutes, BTW
        localend = self._tz.localize(dtend, is_dst = self._daylightSavingsTime)
        utcend = localend.astimezone(pytz.utc)

        dtstamp = utcstamp.strftime("%Y%m%dT%H%M%SZ")
        dtstart = utcstart.strftime("%Y%m%dT%H%M%SZ")
        dtend = utcend.strftime("%Y%m%dT%H%M%SZ")

        uuidStr = str(uuid.uuid4())
        summary = "REF " + gameDetails[2].text
        gameId = gameDetails[3].text
        location = gameDetails[4].text

        ageGroup = gameDetails[5].text
        gender = gameDetails[6].text
        level = gameDetails[7].text
        home = gameDetails[8].text
        away = gameDetails[9].text
        ref = gameDetails[10].text
        ass1 = gameDetails[11].text
        ass2 = gameDetails[12].text
        description = f"""Age: {ageGroup}
        Gender: {gender}
        [Game: {gameId}]
        Level: {level}
        Home: {home}
        Away: {away}
        Referee: {ref}
        Assistant 1: {ass1}
        Assistant 2: {ass2}"""

        icalTemplate = f"""BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Martins Python Program//EN\r\nMETHOD:PUBLISH\r\nBEGIN:VEVENT\r\nUID:{uuidStr}\r\nDTSTAMP:{dtstamp}\r\nCATEGORIES:Official\r\nDTSTART:{dtstart}\r\nDTEND:{dtend}\r\nSUMMARY:{summary}\r\nLOCATION:{location}\r\nDESCRIPTION:{description}\r\nBEGIN:VALARM\r\nTRIGGER:-PT3H\r\nACTION:DISPLAY\r\nDESCRIPTION:REMINDER\r\nEND:VALARM\r\nEND:VEVENT\r\nEND:VCALENDAR"""
        return icalTemplate

class GameOfficials(RefereeWebSite):

    def __init__(self, br):
        super(GameOfficials, self).__init__(br)
        self._baseUrl = "https://www.gameofficials.net"
        self._loginPage = self._baseUrl + "/public/default.cfm"
        self._loginFormInput = { 'username': os.environ['goUsername'],
                                'password': os.environ['goPassword'] }

    def getAssignments(self):
        self._browser.open(self._loginPage)
        self._browser.select_form('form')
        #self._browser.get_current_form().print_summary()
        self._browser['username'] = self._loginFormInput['username']
        self._browser['password'] = self._loginFormInput['password']
        self._browser.submit_selected()


        # check this month
        url = self._baseUrl +  "/Game/myGames.cfm?viewRange=ThisMonth&module=myGames"
        print ("checking this month at {0}...".format(self._baseUrl))
        thisMonthsAssigments = self._findAssignments(url, "this month")
        print("Found {0} assignments this month".format(len(thisMonthsAssigments)))

        # and next month
        today = datetime.date.today()
        p1month = relativedelta(months=1)
        today += p1month
        nextMonth = today.month
        nextMonthStr = today.strftime("%B")
        nextYear = today.year  # uh, why are we reffing in December?
        #url = self._baseUrl + "/Game/myGames.cfm?viewRange=NextMonth&strDay=12/1/19&module=myGames"
        url = self._baseUrl + "/Game/myGames.cfm?module=myGames&viewRange=NextMonth&strDay={0}/1/{1}".format(nextMonth, nextYear)
        print ("Now checking {0} at {1}".format(nextMonthStr, self._baseUrl))
        nextMonthsAssignments = self._findAssignments(url, nextMonthStr)
        print("Found {0} assignments for {1}".format(len(nextMonthsAssignments),
                                                     nextMonthStr))
        return thisMonthsAssigments + nextMonthsAssignments


    def _findAssignments(self, url, currentMonth):
        gamePage = self._browser.open(url)
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

            icalData = self._browser.get(self._baseUrl + aas[1]['href'])
            games.append(icalData.text)

#        if len(games) == 0:
#            print ("No games found for {0}".format(currentMonth))

        return games
