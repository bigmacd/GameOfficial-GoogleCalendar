import csv
import os
import requests
import json
import mechanicalsoup
from refWebSites import GameOfficials
from datetime import datetime as dt
import difflib

gameReportUrl = 'https://www.gameofficials.net/Game/myGames.cfm?module=myGames&viewRange=NextYear&strDay=1/1/19'

# for searching the locations
locationUrl = 'https://www.gameofficials.net/Location/location.cfm'


def getCityStateValuesFromSpreadsheet(csvFile: str) -> dict:
    ''' We can get (download) a spreadsheet ('report') from the web site.  Done manually, 
        this was quick and easy.  The spreadsheet was manually manipulated to remove the 
        assignments that are 'duplicates' (in the case of having multiple games at the same 
        venue consecutively).  Eventually we will just want to pull the list from the 
        website the same way we get current game assignments (and 'de-duplicate').

        In either case (spreadsheet or crawled), the assignments data contains a location
        like 'SIMPSON MS'.  So we gather all these and use this location as the key to 
        store the rest of the data.  
    '''
    retVal = {}
    with open(csvFile, newline='') as fp:
        lines = csv.reader(fp, delimiter=',')
        for line in lines:
            if line[0] == 'XXXXXXXXX':
                break
            location = line[2]
            facility = location[0:location.find('(')]
            
            rightP = location.rfind(')')
            if rightP == -1:
                print("Didn't find city/state in {0}".format(location))
                continue

            leftP = location.rfind('(') + 1
            city, state = location[leftP:rightP].split(',')
            
            city, state, facility = tweakGoData(city, state, facility)

            if facility not in retVal:
                retVal[facility] = {}
                retVal[facility]['city'] = city
                retVal[facility]['state'] = state
                retVal[facility]['count'] = 1
            else:
                retVal[facility]['count'] += 1
    return retVal


def getLatLong(cityStateData: dict) -> dict:
    geoCodeKey = os.environ['geoCodeKey']
    #geocodeUrl = "https://geoservices.tamu.edu/Services/Geocode/WebService/GeocoderWebServiceHttpNonParsedAdvanced_V04_01.aspx?apiKey={0}&version=4.1&format=json&verbose=true&StreetAddress=%20%20%20%20%20%20&city={1}&state={2}&zip=&ratts=PreDirectional,Suffix,PostDirectional,City,Zip&souatts=StreetName,City"
    geocodeUrl = "https://geoservices.tamu.edu/Services/Geocode/WebService/GeocoderWebServiceHttpNonParsedAdvanced_V04_01.aspx?apiKey={0}&version=4.1&format=json&verbose=true&StreetAddress={1}&city={2}&state={3}&zip={4}&ratts=PreDirectional,Suffix,PostDirectional,City,Zip&souatts=StreetName,City"
    for location in cityStateData.items():
        address = location[1]['street']
        city = location[1]['city']
        state = location[1]['state']
        zip = location[1]['zip']
        url = geocodeUrl.format(geoCodeKey, address, city, state, zip)
        response = requests.get(url)
        jsonData = json.loads(response.content)
        latitude = jsonData['OutputGeocodes'][0]['OutputGeocode']['Latitude']
        longitude = jsonData['OutputGeocodes'][0]['OutputGeocode']['Longitude']
        location[1]['latitude'] = latitude
        location[1]['longitude'] = longitude
    return cityStateData


def getMilage(cityStateData: dict) -> dict:
    bingKey = os.environ['bingKey']
    distanceUrl = "https://dev.virtualearth.net/REST/v1/Routes/DistanceMatrix?origins=38.9062046,-77.2777969&destinations={0},{1}&travelMode=driving&key={2}"
    for data in cityStateData.values():
        latitude = data['latitude']
        longitude = data['longitude']
        url = distanceUrl.format(latitude, longitude, bingKey)
        response = requests.get(url)
        jsonData = json.loads(response.content)
        distance = jsonData['resourceSets'][0]['resources'][0]['results'][0]['travelDistance']
        data['distance'] = distance
    return cityStateData


def findLocationDetails(k: str, allLocations: dict) -> dict:
    if k in allLocations:
        return allLocations[k]
    else:
        # let's try some kind of matching thing
        keys = allLocations.keys()
        match = difflib.get_close_matches(k, keys, n=1)
        if (len(match) > 0):
            print("Found a match for {0}: {1}".format(k, match[0]))
            return allLocations[match[0]]
        else:
            return None


def getGoLocationDetails(allAssignments: dict, allLocations: list) -> dict:
    ''' Extract assignment location details from allLocations and update the dictionary
        for each assignment.
    '''
    for k in allAssignments.keys():
        details = findLocationDetails(k, allLocations)
        if details is not None:
            allAssignments[k]['street'] = details['street']
            allAssignments[k]['city'] = details['city']
            allAssignments[k]['state'] = details['state']
            allAssignments[k]['zip'] = details['zip']

    return allAssignments


def getMslLocations():
    pass


def getGoLocations():
    br = mechanicalsoup.StatefulBrowser(soup_config={ 'features': 'lxml'})
    br.addheaders = [('User-agent', 'Chrome')]
    go = GameOfficials(br)
    return go.getLocations()


def tweakGoData(city, state, facility):
    # garbage fucking data in Game Officials
    # fuck fuck fuck
    if city == "MC LEAN":
                city = "MCLEAN"  
    elif facility.startswith("SIMPSON"):
        if city == "ALEXANDRIA":
            facility = "SIMPSON SOCCER"
        else:
            facility = "SIMPSON MS"
    elif facility.startswith("HAYFIELD"):
        facility = "HAYFIELD "
    elif facility.startswith("GEORGE HELLWIG"):
        facility = "HELLWIG PARK"
    return city, state, facility


def doGameOfficials():
   # pull the high level location information from the yearly summary report
    assignmentData = getCityStateValuesFromSpreadsheet("goMileage2019.csv")

    # grab all the location data
    allLocations = getGoLocations()

    # try to get the details of the location (address, zip)
    assignmentData = getGoLocationDetails(assignmentData, allLocations)

    return assignmentData


def doMsl(assignmentData: dict) -> dict:
    return assignmentData


if __name__ == "__main__":
 
    assignmentData = doGameOfficials()
    assignmentData = doMsl(assignmentData)

    # get the lat and long from the tamu web site
    data = getLatLong(assignmentData)

    # get milage from the Bing API
    data = getMilage(assignmentData)
    
    # math
    totalMileage = 0
    for value in assignmentData.values():
        totalMileage += value['count'] * value['distance']
    
    print("Total mileage for {0} is {1}".format(dt.now().year, totalMileage))