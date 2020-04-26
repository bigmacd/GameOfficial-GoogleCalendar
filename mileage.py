import csv
import requests
import json
import mechanicalsoup
from refWebSites import GameOfficials
from datetime import datetime as dt


geoCodeKey = '9a42b593439147d894ed14206d1c7ec0'
bingKey = 'AvkjnSEd_9Ug_wrddndq6K4vaS3pmf0cAiJZhN_LGUum51tWj83cNUFdAh5eAcDt'
gameReportUrl = 'https://www.gameofficials.net/Game/myGames.cfm?module=myGames&viewRange=NextYear&strDay=1/1/19'

# for searching the locations
locationUrl = 'https://www.gameofficials.net/Location/location.cfm'


def getCityStateValues(csvFile: str) -> dict:
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
    geocodeUrl = "https://geoservices.tamu.edu/Services/Geocode/WebService/GeocoderWebServiceHttpNonParsedAdvanced_V04_01.aspx?apiKey={0}&version=4.1&format=json&verbose=true&StreetAddress=%20%20%20%20%20%20&city={1}&state={2}&zip=&ratts=PreDirectional,Suffix,PostDirectional,City,Zip&souatts=StreetName,City"
    geocodeUrlDetail = "https://geoservices.tamu.edu/Services/Geocode/WebService/GeocoderWebServiceHttpNonParsedAdvanced_V04_01.aspx?apiKey={0}&version=4.1&format=json&verbose=true&StreetAddress={1}&city={2}&state={3}&zip={4}&ratts=PreDirectional,Suffix,PostDirectional,City,Zip&souatts=StreetName,City"
    for location in cityStateData.items():
        city = location[1]['city']
        state = location[1]['state']
        url = geocodeUrl.format(geoCodeKey, city, state)
        response = requests.get(url)
        jsonData = json.loads(response.content)
        latitude = jsonData['OutputGeocodes'][0]['OutputGeocode']['Latitude']
        longitude = jsonData['OutputGeocodes'][0]['OutputGeocode']['Longitude']
        location[1]['latitude'] = latitude
        location[1]['longitude'] = longitude
    return cityStateData


def getMilage(cityStateData: dict) -> dict:
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


def getLocationDetails(data: dict) -> dict:
    br = mechanicalsoup.StatefulBrowser(soup_config={ 'features': 'lxml'})
    br.addheaders = [('User-agent', 'Chrome')]
    go = GameOfficials(br)
    for k in data.keys():
        parsed = k.split(" ")
        facility = parsed[0] + " " + parsed[1]

        values = go.getLocationDetails(facility)

        data[k]['street'] = values['street']
        data[k]['city'] = values['city']
        data[k]['state'] = values['state']
        data[k]['zip'] = values['zip']

    return data

def getLocations():
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


if __name__ == "__main__":
    # pull the high level location information from the yearly summary report
    data = getCityStateValues("goMileage2019.csv")

    # grab all the location data
    locations = getLocations()

    # try to get the details of the location (address, zip)
    getLocationDetails(data)

    # get the lat and long from the tamu web site
    data = getLatLong(data)

    # get milage from the Bing API
    data = getMilage(data)
    
    # math
    totalMileage = 0
    for value in data.values():
        totalMileage += value['count'] * value['distance']
    
    print("Total mileage for {0} is {1}".format(dt.now().year, totalMileage))