from poi_classes import OpenTrip
import utils

def main(destination_city, interests):

    print('STARTED')
    print('EXECUTING API')
    string_kinds = utils.get_kinds(interests)
    city = destination_city.split(',')[0]
    api = OpenTrip(city, string_kinds)
    api.execute()
    print('CREATING MARKER LOCATIONS')
    locations = []
    api.store_locations(locations)
    utils.sort_locations_by_rate(locations)
    locations = utils.limit_locations(locations, 50)
    print('CREATING MAP')
    m = utils.create_map_poi(locations, api.lon, api.lat)
    return m