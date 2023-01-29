from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
from datetime import datetime, date
from dataclasses import dataclass, field
import pandas as pd
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
import re
from forex_python.converter import CurrencyRates
from forex_python.converter import CurrencyCodes
from decimal import Decimal

import utils as ut

@dataclass
class Flight:
  origin: str
  destination: str
  departure_date: str
  departure_time: str
  departure_datetime: datetime = field(init=None)
  arrival_time: str
  airlines: str
  duration: int
  n_stops: int
  carbon_footprint: float

  def __post_init__(self) -> None:
    self.departure_datetime = ut.create_full_date(self.departure_date, self.departure_time)
    self.duration = ut.convert_to_minutes(self.duration)
    self.n_stops = ut.convert_num_stops(self.n_stops)
    self.carbon_footprint = ut.convert_carbon_footprint(self.carbon_footprint)
    self.airlines = " / ".join(self.airlines)

@dataclass
class FlyGreen:
    origin: Flight
    destination: Flight
    total_duration: int = field(init=0)
    total_flights: int = field(init=0)
    price: float
    offset: float
    currency: str
    carbon_footprint: int
    clean_flight: bool
    offer_link: str
    provider_name: str
    
    def __post_init__(self):
      self.price = ut.convert_price_to_num(self.price)
      self.total_duration = ut.calculate_total_duration(self.origin, self.destination)
      self.total_flights = ut.calculate_total_flights(self.origin, self.destination)
    
    def create_dict(self):
      origin_dict = self.origin.__dict__.copy()
      origin_dict = ut.add_prefix_keys(origin_dict, 'origin')

      if self.destination:
        destination_dict = self.destination.__dict__.copy()
        destination_dict = ut.add_prefix_keys(destination_dict, 'destination')
      else:
        destination_dict = None

      flight_dict = self.__dict__.copy()
      return_dict = dict()

      return_dict.update(origin_dict)
      flight_dict.pop('origin')

      if destination_dict:
        return_dict.update(destination_dict)
      flight_dict.pop('destination')
      
      return_dict.update(flight_dict)
      return return_dict
  
class FlyGreenScrapper:
  def __init__(
      self, 
      origin: str, 
      destination: str, 
      flight_type: str, 
      adults: int, 
      children: int, 
      infants: int, 
      cabins: str, 
      date_from: str, 
      date_to: str,
      stops: int,
      overnight: bool,
      limit: int = 20,
  ):
    self.html = None
    self.driver = None
    self.options = None
    self.url = 'https://fly.green'
    self.query_url = ''
    self.flight_type = flight_type
    self.adults = adults
    self.children = children
    self.infants = infants
    self.selected_cabins = cabins
    self.fly_from = origin
    self.fly_to = destination
    self.date_from = date_from
    self.date_to = date_to
    self.number_stops = stops
    self.overnight_stopover = overnight
    self.number_pages = 0
    self.next_page = True
    self.limit = limit

  def create_query(self):
    self.query_url += f'{self.url}/search-results/?'
    self.query_url += f'flight_type={self.flight_type}&'
    self.query_url += f'adults={self.adults}&'
    self.query_url += f'children={self.children}&'
    self.query_url += f'infants={self.infants}&'
    self.query_url += f'selected_cabins={self.selected_cabins}&'
    self.query_url += f'fly_from={self.fly_from}&'
    self.query_url += f'fly_to={self.fly_to}&'
    self.query_url += f'date_from={self.date_from}&'
    self.query_url += f'date_to={self.date_to}'
    self.query_url += f''

  def start_driver(self):
    self.create_query()

    if not self.options:
      self.options = webdriver.ChromeOptions()
      self.options.add_argument('--headless')
      self.options.add_argument('--no-sandbox')
      self.options.add_argument('--disable-dev-shm-usage')
    
    if not self.driver:
      self.driver = webdriver.Chrome('chromedriver',options=self.options)

    self.driver.get(self.query_url)
  
  def filter_stops(self):
    id_input = None
    if self.number_stops == -1:
      id_input = 'fr_filter_stops_any'
    elif self.number_stops == 0:
      id_input = 'fr_filter_stops_0'
    elif self.number_stops == 1:
      id_input = 'fr_filter_stops_1'
    elif self.number_stops == 2:
      id_input = 'fr_filter_stops_2'

    input = self.driver.find_element(By.ID, id_input)
    self.driver.execute_script("arguments[0].click();", input)

    if self.overnight_stopover:
      id_check = 'fr_filter_stops_allow_overnight'
      check = self.driver.find_element(By.ID , id_check)
      self.driver.execute_script("arguments[0].click();", input)

  def start_scrapper(self):
    page_content = self.driver.page_source
    self.html = BeautifulSoup(page_content, 'lxml')
  
  def get_flights_page(self):
    return self.html.find_all('div' , class_ = 'col-lg-9 _col_itinerary')
  
  def get_intineraries_page(self):
    return self.html.find_all('div', class_ = 'modal-content')
  
  def get_prices_page(self):
    return self.html.find_all('div', class_ = 'col-lg-3 _col_pricing')
  
  def get_info_pricing(self, pricing_html):
    price = pricing_html.find('span', class_ = '_val')
    price = price.text if price else None

    booking_options = pricing_html.find('a', class_ = '_btn_itinerary_booking_options ')
    if not booking_options:
      booking_options = pricing_html.find('a', class_ = '_btn_itinerary_booking_options')
    booking_options_not_clean = pricing_html.find(
        'a', class_ = '_btn_itinerary_booking_options _it_more_co2'
    )
    
    if booking_options:
      offset = int(booking_options['data-offset-val'])
      link_offer = booking_options['data-deep-link']
      offer_provider = booking_options['data-provider']
      total_co2 = int(booking_options['data-co2-total-val'])
    elif booking_options_not_clean:
      print('not clean flight')
      offset = int(booking_options_not_clean['data-offset-val'])
      link_offer = booking_options_not_clean['data-deep-link']
      offer_provider = booking_options_not_clean['data-provider']
      total_co2 = int(booking_options_not_clean['data-co2-total-val'])
    else:
      print('not found')
      print(pricing_html.find(class_= '_btn_itinerary_booking_options'))
      offset = None
      link_offer = None
      offer_provider = None
      total_co2 = None
    
    return price, offset, link_offer, offer_provider, total_co2
  
  def get_airlines(self, intinerary_html):
    divs = intinerary_html.find_all('div')
    to_origin = False
    to_destination_airlines = []
    to_origin_airlines = []
    for d in divs:
      if '_m_row_dst_nights' in d['class']:
        to_origin = True
      if '_m_airline_name' in d['class']:
        if to_origin:
          if d.text not in to_origin_airlines:
            to_origin_airlines.append(d.text)
        else:
          if d.text not in to_destination_airlines:
            to_destination_airlines.append(d.text)
    
    return to_destination_airlines, to_origin_airlines

  def extract_flight_info(self, flights_html, intinerary_info, pricing_info):
    cities = flights_html.find_all('span', class_ = '_city') 
    # departure_dates = flights_html.find_all('div', class_ = '_departure_date')
    times = flights_html.find_all('span', class_ = '_time')
    durations = flights_html.find_all('span', class_ = '_duration')
    num_of_stops = flights_html.find_all('span', class_ = '_nof_stops')

    co2_emissions = intinerary_info.find_all('div', class_ = '_m_trip_co2')
    to_destination_airlines, to_origin_airlines = self.get_airlines(intinerary_info)

    price, offset, link_offer, offer_provider, total_co2 = self.get_info_pricing(pricing_info)
    currency = '$'

    if pricing_info.find_all('span')[-1].text == 'book this flight':
      clean_flight = True
    else:
      clean_flight = False


    if self.flight_type == 'round':

      origin_city, destination_city = cities[0].text, cities[1].text
      origin_departure_date, destination_departure_date = (self.date_from, #departure_dates[0].text, 
                                                          self.date_to) #departure_dates[1].text)
      origin_d_time, destination_a_time, destination_d_time, origin_a_time = (
          times[0].text, times[1].text, times[2].text, times[3].text
      )
      duration_to_destination, duration_to_origin = (durations[0].text, 
                                                    durations[1].text)
      num_stops_to_destination, num_stops_to_origin = (num_of_stops[0].text.replace(" ", "").strip(),
                                                      num_of_stops[1].text.replace(" ", "").strip())
      
      airlines_to_destination, airlines_to_origin = [], []
      co2_to_destination, co2_to_origin = co2_emissions[0].text, co2_emissions[1].text
    
    elif self.flight_type == 'oneway':
      origin_city, destination_city = cities[0].text, cities[1].text
      origin_departure_date = self.date_from
      origin_d_time, destination_a_time = times[0].text, times[1].text
      duration_to_destination = durations[0].text
      num_stops_to_destination = num_of_stops[0].text.replace(" ", "").strip()
      airlines_to_destination = []
      co2_to_destination = co2_emissions[0].text


    flight_to_destination = Flight(origin=origin_city,
                                  destination=destination_city,
                                  departure_date=origin_departure_date,
                                  departure_time=origin_d_time,
                                  arrival_time=destination_a_time,
                                  duration=duration_to_destination,
                                  airlines=to_destination_airlines,
                                  n_stops=num_stops_to_destination,
                                  carbon_footprint=co2_to_destination,
                                  )
    
    
    if self.flight_type == 'round':
      flight_to_origin = Flight(origin=destination_city,
                                  destination=origin_city,
                                  departure_date=destination_departure_date,
                                  departure_time=destination_d_time,
                                  arrival_time=origin_a_time,
                                  duration=duration_to_origin,
                                  airlines=to_origin_airlines,
                                  n_stops=num_stops_to_origin,
                                  carbon_footprint=co2_to_origin,
                                  )
      
      flight_info = FlyGreen(origin=flight_to_destination, 
                            destination=flight_to_origin,
                            price=price,
                            offset=offset,
                            currency=currency,
                            carbon_footprint=total_co2,
                            clean_flight=clean_flight,
                            offer_link=link_offer,
                            provider_name=offer_provider)


    else:
      flight_info = FlyGreen(origin=flight_to_destination, 
                            destination=None,
                            price=price,
                            offset=offset,
                            currency=currency,
                            carbon_footprint=total_co2,
                            clean_flight=clean_flight,
                            offer_link=link_offer,
                            provider_name=offer_provider)
    
    return flight_info

  def create_flight_objects(self, list_flights: list):
    flights = self.get_flights_page()
    intineraries = self.get_intineraries_page()
    prices = self.get_prices_page()

    for f_html, i_html, p_html in zip(flights, intineraries, prices):
      list_flights.append(self.extract_flight_info(f_html, i_html, p_html))
    
    return list_flights
  
  def get_number_page_results(self):
    page_links = self.html.find_all('a', class_ = 'page-link')
    if page_links:
      self.number_pages = max(
          [int(p['data-page']) for p in page_links if len(p['class']) == 1]
      )
    else:
      self.number_pages = 0
  
  def click_next_page(self):
    next_button = self.driver.find_elements(By.XPATH, '//*[@id="flights_search_pagination"]/ul/li/a')[-1]
    next_button_value = int(next_button.get_attribute("data-page"))
    last_button_value = int(
        self.driver.find_elements(
        By.XPATH, '//*[@id="flights_search_pagination"]/ul/li/a'
        )[-2].get_attribute("data-page")
    )
    print(f'{next_button_value}/{last_button_value}')
    if next_button_value != last_button_value and next_button_value +1 <= self.limit:
      self.driver.execute_script("arguments[0].click();", next_button)
    else:
      self.next_page = False
  
  def click_first_page(self):
    first_button = self.driver.find_elements(By.XPATH, '//*[@id="flights_search_pagination"]/ul/li/a')[1]
    self.driver.execute_script("arguments[0].click();", first_button)
    self.next_page = True
  
  def get_all_flights(self, list_flights):
    if self.number_pages:
      while self.next_page:
        self.create_flight_objects(list_flights)
        time.sleep(2)
        self.click_next_page()
        self.start_scrapper()

      self.click_first_page()
  
    
  def init_scrapper(self):
    self.start_driver()
    self.start_scrapper()
    self.get_number_page_results()