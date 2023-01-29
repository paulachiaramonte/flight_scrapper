import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

def create_pie_plot_airlines(df):
  airlines_all = list(df['origin_airlines']) 
  if 'destination_airlines' in df.columns:
    airlines_all += list(df['destination_airlines'])
  
  # Create an empty list
  result = []
  for elem in airlines_all:
      split = elem.split('/')
      for s in split:
          result.append(s.strip())
  
  airlines = pd.Series(result).value_counts()
  labels = list(airlines.index)
  sizes = list(airlines)
  return labels, sizes
  fig1, ax1 = plt.subplots()
  ax1.pie(sizes, labels=labels, autopct='%1.1f%%',
          shadow=True, startangle=90)
  ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
  plt.title('Ratio of Airline flights')
  return fig1

def plot_range_prices(df):
    return df.price
#   fig, ax = plt.subplots()

    ax.hist(df.price, bins=20)
    ax.set_title('Range of Flight Prices')
    plt.show()
  
#   return fig

def pie_plot_clean_flights(df):
  airlines = pd.Series(df.clean_flight).value_counts()
  labels = list(airlines.index)
  sizes = list(airlines)
  return labels, sizes

def show_pie_plots(df):
    fig, axs = plt.subplots(1,3, figsize=(20,5))

    labels, sizes = create_pie_plot_airlines(df)

    axs[0].pie(sizes, labels=labels, autopct='%1.1f%%',
          shadow=True, startangle=90)
    axs[0].set_title('Ratio of Airline flights')

    axs[1].hist(df.price, bins=20)
    axs[1].set_title('Range of Flight Prices ($)')

    labels, sizes = pie_plot_clean_flights(df)
    axs[2].pie(sizes, labels=labels, autopct='%1.1f%%',
          shadow=True, startangle=90)
    axs[2].set_title('Ratio of Clean flights')

    return fig

def show_line_plots(df):
    fig, axs = plt.subplots(2,1,figsize=(20,10))
    axs[0].plot(df.groupby(['destination_departure_time'])['price'].mean())
    axs[0].set_title('Mean Price per departure time to destination')

    axs[1].plot(df.groupby(['origin_departure_time'])['price'].mean())
    axs[1].set_title('Mean Price per departure time back to origin')

    return fig


def return_best_flight(df, preferences):
    map_preferences = {
        'Cheapest Flight': 'price',
        'Lower CO2 Emissions': 'carbon_footprint',
        'Lower Duration': 'total_duration',
        'Lower Number of Stops': 'total_flights'
    }
    sort_cols = [map_preferences[p] for p in preferences]
    result_df = df.sort_values(by=sort_cols).head(1)
    return result_df

def return_chepeast_flight(df, preferences):
    map_preferences = {
        'Cheapest Flight': 'price',
        'Lower CO2 Emissions': 'carbon_footprint',
        'Lower Duration': 'total_duration',
        'Lower Number of Stops': 'total_flights'
    }
    sort_cols = [i for i in preferences]
    sort_cols = [map_preferences[p] for p in sort_cols]
    sort_cols.remove('price')
    sort_cols.insert(0, 'price')
    return df.sort_values(by= sort_cols).head(1)

def return_lowest_emissions(df, preferences):
    map_preferences = {
        'Cheapest Flight': 'price',
        'Lower CO2 Emissions': 'carbon_footprint',
        'Lower Duration': 'total_duration',
        'Lower Number of Stops': 'total_flights'
    }
    sort_cols = [i for i in preferences]
    sort_cols = [map_preferences[p] for p in sort_cols]
    sort_cols.remove('carbon_footprint')
    sort_cols.insert(0, 'carbon_footprint')
    return df.sort_values(by= sort_cols).head(1)

def return_shortest_flights(df, preferences):
    map_preferences = {
        'Cheapest Flight': 'price',
        'Lower CO2 Emissions': 'carbon_footprint',
        'Lower Duration': 'total_duration',
        'Lower Number of Stops': 'total_flights'
    }
    sort_cols = [i for i in preferences]
    sort_cols = [map_preferences[p] for p in sort_cols]
    sort_cols.remove('total_duration')
    sort_cols.insert(0, 'total_duration')
    return df.sort_values(by= sort_cols).head(1)

def return_smaller_n_stops(df, preferences):
    map_preferences = {
        'Cheapest Flight': 'price',
        'Lower CO2 Emissions': 'carbon_footprint',
        'Lower Duration': 'total_duration',
        'Lower Number of Stops': 'total_flights'
    }
    sort_cols = [i for i in preferences]
    sort_cols = [map_preferences[p] for p in sort_cols]
    sort_cols.remove('total_flights')
    sort_cols.insert(0, 'total_flights')
    return df.sort_values(by= sort_cols).head(1)

def return_flight_info(df, return_flight):

    if return_flight:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### To Destination Flight")
            st.markdown("**Departure time**: {}".format(df['origin_departure_time'].values[0]))
            st.markdown("**Arrival time**: {}".format(df['origin_arrival_time'].values[0]))
            st.markdown("**Duration**: {}".format(df['origin_duration'].values[0]))
            st.markdown("**Airlines**: {}".format(df['origin_airlines'].values[0]))
            st.markdown("**Number of Stops**: {}".format(df['origin_n_stops'].values[0]))

        with col2:
            st.markdown("### Return Flight")
            st.markdown("**Departure time**: {}".format(df['destination_departure_time'].values[0]))
            st.markdown("**Arrival time**: {}".format(df['destination_arrival_time'].values[0]))
            st.markdown("**Airlines**: {}".format(df['destination_airlines'].values[0]))
            st.markdown("**Duration**: {}".format(df['destination_duration'].values[0]))
            st.markdown("**Number of Stops**: {}".format(df['destination_n_stops'].values[0]))
    else:
        st.markdown("### To Destination Flight")
        st.markdown("**Departure time**: {}".format(df['origin_departure_time'].values[0]))
        st.markdown("**Arrival time**: {}".format(df['origin_arrival_time'].values[0]))
        st.markdown("**Duration**: {}".format(df['origin_duration'].values[0]))
        st.markdown("**Airlines**: {}".format(df['origin_airlines'].values[0]))
        st.markdown("**Number of Stops**: {}".format(df['origin_n_stops'].values[0]))

    st.markdown("### Info:")
    st.markdown("**Price**: {} {}".format(df['price'].values[0], df['currency'].values[0]))
    st.markdown("**Carbon Footprint**: {} CO2e".format(df['price'].values[0]))
    st.markdown('[Offer Link Here]({})'.format(df['offer_link'].values[0]))
import utils
def return_flight_info_short(df, destination_flight):
    st.markdown("**Total Duration**: {}".format(utils.convert_from_minutes(df['total_duration'].values[0])))
    if destination_flight:
        st.markdown("**Number of Stops**: {}".format(df['total_flights'].values[0] -2))
    else:
        st.markdown("**Number of Stops**: {}".format(df['total_flights'].values[0] -1))
    st.markdown("**Price**: {} {}".format(df['price'].values[0], df['currency'].values[0]))
    st.markdown("**Carbon Footprint**: {} CO2e".format(df['price'].values[0]))
    st.markdown('[Offer Link Here]({})'.format(df['offer_link'].values[0]))



