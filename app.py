import streamlit as st
from streamlit_folium import st_folium
import utils
import utils
import pandas as pd
import flights
import matplotlib.pyplot as plt
import poi
import plots

city_codes = utils.get_city_codes()

# Create a box to group the input objects
box = st.empty()

# Add a title to the container
box.title("Trip Planner")

# Create a list of possible values
possible_values = list(city_codes.keys())

# Ask the user for the type of trip
trip_type = st.radio("Type of trip:", ["Round trip", "One way"])

origin_city =st.selectbox("Origin city:", possible_values)

destination_city =st.selectbox("Destination city:", possible_values)

if destination_city != origin_city:
  st.success('The destination city is valid')
else:
  st.error('The destination city is not valid')
  st.stop()

# Create a date input for the departure date
departure_date =st.date_input("Departure date:")

if trip_type == "One way":
    st.empty()
    return_date = None
else:
    # Create a date input for the return date
    return_date =st.date_input("Return date:", value = departure_date)

if return_date:
    if return_date > departure_date:
        st.success('The return date is valid')
    else:
        st.error('The return date is not valid')
        st.stop()

st.write('Flight preferences')

# Ask the user for the type of cabin
cabin_type = st.selectbox("Type of cabin:", ["Economy", "Business"])

# Ask the user for the number of stops
num_stops = st.selectbox("Number of stops:", ["Any", "Direct", "One stop", "Two stops", "More than two stops"])

# Ask the user if they want an overnight flight
overnight = st.checkbox("Overnight flight")

# Create inputs for the number of adults, children, and infants
num_adults =st.number_input("Number of adults:", step = 1, min_value=1)
num_children =st.number_input("Number of children:", step = 1, min_value=0)
num_infants =st.number_input("Number of infants:", step= 1, min_value=0)

time_range_to_destination = st.slider('Select the time range for departure time to destination:', min_value=0, 
                                        max_value=24, 
                                        value=(0,24), 
                                        step=1,
                                        key = 'to_destination')
# Extract the minimum and maximum time of departure from the time range
min_time_to_destination, max_time_to_destination = time_range_to_destination

if trip_type == "Round trip":
    time_range_to_origin = st.slider('Select the time range for departure time back to origin:', 
                                    min_value=0, 
                                    max_value=24, 
                                    value=(0,24), 
                                    step=1,
                                    key = 'to_origin')
    # Extract the minimum and maximum time of departure from the time range
    min_time_to_origin, max_time_to_origin = time_range_to_origin

preferences = st.multiselect('Select in order your preferences for searching for a flight:',
                             ['Cheapest Flight', 'Lower CO2 Emissions', 'Lower Duration', 'Lower Number of Stops'])

# Sort the preferences in the order selected by the user
sorted_preferences = sorted(preferences, key=lambda x: preferences.index(x))
st.write('Point of Interests preferences')
# Create a list of names
names = list(utils.get_categories_poi().keys())

# Create a checkbox for the list of names
selected_interests =st.multiselect("What are your main interests?", names)

## TODO: Add filter to select priority between price, co2 emissions, duration and n_stops

# Create a button to submit the input
if st.button("Submit"):

    origin = city_codes.get(origin_city)
    destination = city_codes.get(destination_city)

    if origin and destination:
        
        flight_type = "round" if trip_type == "Round trip" else "oneway"

        if num_stops == "Any":
            stops = -1 
        elif num_stops == "Direct":
            stops = 0
        elif num_stops == "One stop":
            stops = 1
        elif num_stops == "Two stops":
            stops = 2 
        elif num_stops == "More than two stops":
            stops = 3
        else:
            stops = -1

        if overnight:
            night = True
        else:
            night = False
        
        if cabin_type == 'Economy':
            cabins='M'
        elif cabin_type == 'Business':
            cabins = 'C'
        else:
            cabins='M'

        with st.spinner(f'Searching for flights from {origin_city} to {destination_city}, please wait ...'):
        
            flights_df = flights.main(origin, 
                                    destination,
                                    type_of_destination=flight_type,
                                    num_adults=num_adults,
                                    num_children=num_children,
                                    num_infants=num_infants,
                                    date_from=str(departure_date),
                                    date_to=str(return_date),
                                    cabin=cabins,
                                    stops=num_stops,
                                    overnight=overnight)

        if flights_df.empty:
            st.error('No flights with your desire input parameters')
            st.stop()

        # Filter time of arrival 
        filt_dest= pd.to_datetime(flights_df['origin_departure_time'], format='%I:%M %p')
        filt_ori = pd.to_datetime(flights_df['destination_departure_time'], format='%I:%M %p')
        search_df = flights_df[(filt_dest.dt.hour < max_time_to_destination) & (filt_dest.dt.hour > min_time_to_destination) &
                (filt_ori.dt.hour < max_time_to_destination) & (filt_ori.dt.hour > min_time_to_destination)]
                
        st.subheader('Flights offers for your next trip:')
        # Show the head of the dataframe        
        # st.write(flights_df.sort_values(by='price').head())
        st.write('Best Flight according your priorities')
        st.markdown("**{} to {}**".format(flights_df['origin_origin'].values[0], flights_df['origin_destination'].values[0]))
        best_flight = plots.return_best_flight(search_df, sorted_preferences)
        plots.return_flight_info(best_flight, return_date)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('#### Chepeast Flight')
            flight1 = plots.return_chepeast_flight(flights_df, sorted_preferences)
            plots.return_flight_info_short(flight1, return_date)
            st.markdown('#### Most eco friendly flight')
            flight2 = plots.return_lowest_emissions(flights_df, sorted_preferences)
            plots.return_flight_info_short(flight2,return_date)
        with col2:
            st.markdown('#### Shortest Flight')
            flight3 = plots.return_shortest_flights(flights_df, sorted_preferences)
            plots.return_flight_info_short(flight3,return_date)
            st.markdown('#### Shorter number of stops')
            flight4 = plots.return_smaller_n_stops(flights_df, sorted_preferences)
            plots.return_flight_info_short(flight4,return_date)

        st.subheader('Analysis of Flights offers for your next trip:')
        fig = plots.show_pie_plots(flights_df)
        st.pyplot(fig)
        fig2 = plots.show_line_plots(flights_df)
        st.pyplot(fig2)
   
        with st.spinner(f'Searching for places suggested for you in {destination_city}, please wait ..'):
            m = poi.main(destination_city, selected_interests)

        if not m:
            st.error('No places with related with your interests')
            st.stop()
        st.subheader('Suggested Places given you main interests:')
        
        st.write(m, style="width: 3000px; height: 2000px;")
 


