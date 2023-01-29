from dataclasses import dataclass, field
import requests
import json

@dataclass
class Location:
  name:str
  latitude:float
  longitude:float
  distance:float
  rate:float
  osm:str
  wikidata:str
  kinds:str
  main:str=field(init=False)

  def __post_init__(self):
    # Split the string into a list of words
    word_list = self.kinds.split(",")

    # Convert the underscores to spaces and capitalize the first letter of each word
    word_list = [word.replace("_", " ").capitalize() for word in word_list]

    # Create the HTML code for the bullet points
    html = "<ul>\n"
    for word in word_list:
      html += "  <li>" + word + "</li>\n"
    html += "</ul>"

    # Print the HTML code
    self.kinds = html
    self.main = word_list[0]

class OpenTrip:
  def __init__(self, city: str, kinds:str):
    self.url = 'https://api.opentripmap.com/0.1/ru/places/radius'
    self.api_key = '5ae2e3f221c38a28845f05b6ea129edf566f0f2348c88721790aeebb'
    self.headers = dict()
    self.params = dict()
    self.city = city
    self.lat = None
    self.lon = None
    self.kinds = kinds
    self.response = None
  
  def get_coordinates(self):
    url = 'https://api.opentripmap.com/0.1/en/places/geoname'
    params = {
        'name':self.city,
        'apikey':'5ae2e3f221c38a28845f05b6ea129edf566f0f2348c88721790aeebb'
    }
    r = requests.get(url, params=params)
    city = json.loads(r.content)
    self.lat = city.get('lat', None)
    self.lon = city.get('lon', None)

  def define_values(self):
    self.headers['accept'] = 'application/json'

    self.params['radius'] = 10000
    self.params['lat'] = self.lat
    self.params['lon'] = self.lon
    self.params['kinds'] = self.kinds
    self.params['apikey'] = self.api_key
    self.params['rate'] = 3 # Popularity


  def execute(self):
    # Get coordinates of city
    self.get_coordinates()
    # Define values of parameters and headers for request
    self.define_values()
    # Get request
    response = requests.get(self.url, params=self.params, headers=self.headers)
    #Check if error:
    json_r = json.loads(response.content)
    if 'error' in json_r:
      self.response = None
    else:
      self.response = json_r
    
    print('JSON CREATED')

  def store_locations(self, list_locations):
    for loc in self.response['features']:
      if loc['properties']['rate'] >= 1:
        properties = loc['properties']
        geometry = loc['geometry']

        name = properties['name']
        latitude, longitude = tuple(geometry['coordinates'])
        distance = properties.get('dist', None)
        rate = properties.get('rate', None)
        osm = properties.get('osm', None)
        wikidate = properties.get('wikidata', None)
        kinds = properties.get('kinds', None)

        new_loc = Location(name=name,
                           latitude=latitude,
                           longitude=longitude,
                           distance=distance,
                           rate=rate,
                           osm=osm,
                           wikidata=wikidate,
                           kinds=kinds
        )
        list_locations.append(new_loc)
