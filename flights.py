from data_classes import FlyGreenScrapper
from google_flight import GoogleFlightsScrapper
import pandas as pd
import utils

def main(origin, 
    destination, 
    type_of_destination,
    num_adults,
    num_children,
    num_infants,
    date_from,
    date_to,
    cabin='M',
    stops=-1,
    overnight=False,
    ):
    print(origin, destination)
    scrapper_green = FlyGreenScrapper(origin=origin, destination = destination,
                           flight_type=type_of_destination, 
                           adults=num_adults, 
                           children=num_children, 
                           infants=num_infants,
                           cabins=cabin,
                           date_from=date_from,
                           date_to=date_to,
                           stops=stops, overnight=overnight, limit=10
                           )

    scrapper_green.init_scrapper()
    list_flights = []
    scrapper_green.get_all_flights(list_flights)
    flights_df_green = utils.create_flights_df(list_flights)
    print(flights_df_green.head())
    utils.save_df_to_csv(flights_df_green)
    scrapper_green.driver.quit()

    if type_of_destination == 'round':
        scrapper = GoogleFlightsScrapper(origin=origin, 
                           destination =destination,
                           date_from=date_from,
                           oneway = False,
                           date_to=date_to)
    else:
        scrapper = GoogleFlightsScrapper(origin=origin, 
                           destination =destination,
                           date_from=date_from,
                           oneway = True,
                           date_to=None)

    df = scrapper.init_scrapper()
    if 'destination_departure_datedestination_departure_time' in df.columns:
        df = df.drop(columns = 'destination_departure_datedestination_departure_time')
    
    if not df.empty:
        flights_df_green = pd.concat([flights_df_green, df], axis = 0)
    return flights_df_green

if __name__ == "__main__":
    main()