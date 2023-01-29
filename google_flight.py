
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
class GoogleFlightsScrapper:
  def __init__(
      self, 
      origin: str, 
      destination: str, 
      date_from: str, 
      oneway: bool,
      date_to: str = None,
  ):
    self.html = None
    self.driver = None
    self.url = 'https://www.google.com/travel/flights?'
    self.query_url = ''
    self.fly_from = origin
    self.fly_to = destination
    self.date_from = date_from
    self.date_to = date_to
    self.oneway = oneway
    self.grouped = []
    self.grouped_ret = []
    self.query_url_ret = ''
    self.df = None
    self.orig_list = []
    self.ret_list = []
    self.query_url_complete = ''



  def create_query(self):
    self.query_url += f'{self.url}q=Flights%20to%20{self.fly_to}%20from%20{self.fly_from}%20on%20{self.date_from}' #%20through%20{self.date_to}'  


  def create_query_ret(self):
    self.query_url_ret += f'{self.url}q=Flights%20to%20{self.fly_from}%20from%20{self.fly_to}%20on%20{self.date_to}' #%20through%20{self.date_to}' 
    self.query_url_complete += f'{self.url}q=Flights%20to%20{self.fly_to}%20from%20{self.fly_from}%20on%20{self.date_from}%20through%20{self.date_to}'  

  @staticmethod
  def get_flight_elements(d):
    return d.find_element(by = By.XPATH, value = '//body[@id = "yDmH0d"]').text.split('\n')


  def make_url_request(self):
    self.create_query()
    # Instantiate driver and get raw data
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')


    self.driver = webdriver.Chrome('chromedriver',options=options)
    self.driver.get(self.query_url)

    # Waiting and initial XPATH cleaning
    # WebDriverWait(self.driver, timeout = 20).until(lambda d: len(self.get_flight_elements(d)) > 10)
    time.sleep(30)
    self.html = BeautifulSoup(self.driver.page_source, 'lxml')
    results = self.get_flight_elements(self.driver)
    
    self.driver.quit()

    return results

  def make_url_request_ret(self):
    self.create_query_ret()
    # Instantiate driver and get raw data
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')


    self.driver = webdriver.Chrome('chromedriver',options=options)
    self.driver.get(self.query_url_ret)

    # Waiting and initial XPATH cleaning
    # WebDriverWait(self.driver, timeout = 10).until(lambda d: len(self.get_flight_elements(d)) > 100)
    time.sleep(30)
    results = self.get_flight_elements(self.driver)

    self.driver.quit()

    return results

  def get_results(self):

      results = self.make_url_request()

      # Data cleaning
      flight_info = self.get_info(results) # First, get relevant results
      self.grouped = self.partition_info(flight_info) # Partition list into "flights"
      self.parse_columns()
      return
  def get_results_ret(self):
      results = self.make_url_request_ret()

      # Data cleaning
      flight_info = self.get_info(results) # First, get relevant results
      self.grouped_ret = self.partition_info(flight_info) # Partition list into "flights"
      self.parse_columns_ret()
      return  # "Transpose" to data frame

  @staticmethod
  def get_info(res):
      info = []
      collect = False
      for r in res:

          if 'more flights' in r:
              collect = False

          if collect and 'price' not in r.lower() and 'prices' not in r.lower() and 'other' not in r.lower() and ' – ' not in r.lower():
              info += [r]

          if r == 'Sort by:':
              collect = True
              
      return info


  @staticmethod
  def partition_info(info):
      grouped = []
      one_list = []
      start = False
      destin = False
      for i in range(len(info)-1):
        if len(info[i+1]) == 3:
          if info[i+1].isupper() == True:
            if start == False:
              start = True
            elif destin == False:
              destin = True
            else:
              start, destin = True, False
              grouped.append(one_list)
              one_list = []

        if info[i] != 'SEPARATE TICKETS BOOKED TOGETHER':
          one_list.append(info[i])     
      return grouped

  def create_df(self): 
      columns = ['origin_origin' , 'origin_destination' ,'origin_departure_date','origin_departure_time' ,'origin_arrival_time' ,'origin_airlines' ,'origin_duration' ,'origin_n_stops' ,'origin_carbon_footprint' ,'origin_departure_datetime', 'destination_origin' ,'destination_destination'  ,'destination_departure_date' 'destination_departure_time',  'destination_arrival_time' ,'destination_airlines'  ,'destination_duration' ,'destination_n_stops' , 'destination_carbon_footprint'  ,'destination_departure_datetime' ,'price'  , 'offset' , 'currency', 'carbon_footprint' , 'clean_flight' ,'offer_link', 'provider_name' , 'total_duration', 'total_flights']
      self.df = pd.DataFrame({col: [] for col in columns})
      return 
  def create_df_oneway(self): #cambiartrrnf
      columns = ['origin' , 'destination' ,'departure_date','departure_time' ,'arrival_time' ,'airlines' ,'duration' ,'n_stops' ,'carbon_footprint' ,'departure_datetime', 'price','clean_flight', 'currency', 'offer_link']
      self.df = pd.DataFrame({col: [] for col in columns})
      return 

  def get_df(self):
      if self.oneway == False and self.date_to == None:
        print('Please provide a return date')
        return
      self.get_results()
      if self.oneway == False:
          self.create_df()
          self.get_results_ret()
          self.addtodf()
      else:
        self.create_df_oneway()
        self.addtodf_oneway()
      print('Done!') 
      return self.df

  def addtodf_oneway(self):

      # For each "flight"
      for g in self.grouped:

          origin = g[1]
          destination = g[3]
          depart_time = g[0]
          arrival_time = g[2]

          c_price = g[4]

          curr = re.findall(r'\D', c_price)
          for r in curr:
            if r == ',':
              curr.remove(r)
          c_symbol = ''
          for i in curr:
            if i != '.' :
              c_symbol += i

          
          c_list = re.findall("[$]?(\d[\d,.]*)", c_price)
          c_amount = ''
          for s in c_list:
            c_amount += str(s)
          c_amount = c_amount.replace(',','')
          c_name = self.get_currency_name(c_symbol)
          price = self.convert_to_usd(c_amount,c_name)

          s = g[6]

          if list(s)[0].isdigit() == False: 
            sep = re.split(r'\d', s)
            stops = sep[0]
            _ , end = s.split(stops)
          else:
            beg1 , end =(s.split('stop'))
            stops = f'{beg1} stops'
          numbs = (re.findall("\d+", end))
          if len(numbs) == 1:
            numbs.append('00')
          duration = f'{numbs[0]} hr {numbs[1]} min'
          m = re.search(r'[A-Z]', end)
          airline = end[m.start():]

          co2_emission = 'No Information'
          if len(g) >7:
              co2_emission = g[7]
          depart_date = f'{self.date_from} {depart_time}'

          clean_flight = 'No Information'
          if co2_emission != 'No Information':
              value = list(co2_emission.split(' ')[0])[0]
              if value == 'A' or value == '+':
                  clean_flight = 'False'
              elif value == '-':
                  clean_flight = 'True'

          row =  {'origin' : origin, 
              'destination' : destination,
              'departure_date' : self.date_from,
              'departure_time' : depart_time,
              'arrival_time' : arrival_time,
              'airlines' : airline,
              'duration' : duration,
              'n_stops' : stops,
              'carbon_footprint' : co2_emission,
              'departure_datetime': depart_date, 
              'price' : price,
              'clean_flight': clean_flight,
              'currency' : c_name, 
              'offer_link': self.query_url }

          # ?
          self.df = self.df.append(row, ignore_index = True)
      return
  def parse_columns(self):
      for g in self.grouped:

          origin = g[1]
          destination = g[3]
          depart_time = g[0]
          arrival_time = g[2]

          c_price = g[4]

          curr = re.findall(r'\D', c_price)
          for r in curr:
            if r == ',':
              curr.remove(r)
          c_symbol = ''
          for i in curr:
            if i != '.' :
              c_symbol += i

          
          c_list = re.findall("[$]?(\d[\d,.]*)", c_price)
          c_amount = ''
          for s in c_list:
            c_amount += str(s)
          c_amount = c_amount.replace(',','')
          c_name = self.get_currency_name(c_symbol)
          price = self.convert_to_usd(c_amount,c_name)

          s = g[6]

          if list(s)[0].isdigit() == False: 
            sep = re.split(r'\d', s)
            stops = sep[0]
            _ , end = s.split(stops)
          else:
            beg1 , end =(s.split('stop'))
            stops = f'{beg1}stops'
          numbs = (re.findall("\d+", end))
          if len(numbs) == 1:
            numbs.append('00')
          duration = f'{numbs[0]} hr {numbs[1]} min'
          m = re.search(r'[A-Z]', end)
          airline = end[m.start():]

          co2_emission = 'No Information'
          if len(g) >7:
              co2_emission = g[7]
          depart_date = f'{self.date_from} {depart_time}'

          clean_flight = 'No Information'
          if co2_emission != 'No Information':
              value = list(co2_emission.split(' ')[0])[0]
              if value == 'A' or value == '+':
                  clean_flight = 'False'
              elif value == '-':
                  clean_flight = 'True'

          
          row =  {
            'origin_origin' : origin, 
            'origin_destination' : destination,
            'origin_departure_date' : self.date_from,
            'origin_departure_time' : depart_time,
            'origin_arrival_time' : arrival_time,
            'origin_airlines' : airline,
            'origin_duration' : duration,
            'origin_n_stops' : stops,
            'origin_carbon_footprint' : co2_emission,
            'origin_departure_datetime': depart_date, 
            'origin_clean_flight':clean_flight,
            'price1':price
            }

          # ?
          self.orig_list.append(row)
      return

  def parse_columns_ret(self):

      for g_ret in self.grouped_ret:
          ret_origin = g_ret[1]


          ret_destination = g_ret[3]
          ret_depart_time = g_ret[0]
          ret_arrival_time = g_ret[2]

          ret_c_price = g_ret[4]

          ret_curr = re.findall(r'\D', ret_c_price)
          for r in ret_curr:
            if r == ',':
              ret_curr.remove(r)
          c_symbol = ''
          for i in ret_curr:
            if i != '.' :
              c_symbol += i

          ret_c_list = re.findall(("[$]?(\d[\d,.]*)"), ret_c_price)
          ret_c_amount = ''
          for s in ret_c_list:
            ret_c_amount += str(s)
          ret_c_amount = ret_c_amount.replace(',','')
          ret_c_name = self.get_currency_name(c_symbol)
          ret_price = self.convert_to_usd(ret_c_amount,ret_c_name)

          ret_s = g_ret[6]
          if list(ret_s)[0].isdigit() == False: 
            sep = re.split(r'\d', ret_s)
            ret_stops = sep[0]
            _ , end = ret_s.split(ret_stops)
          else:
            beg1 , end =(ret_s.split('stop'))
            ret_stops = f'{beg1} stops'
          numbs = (re.findall("\d+", end))
          if len(numbs) == 1:
            numbs.append('00')
          ret_duration = f'{numbs[0]} hr {numbs[1]} min'
          m = re.search(r'[A-Z]', end)
          ret_airline = end[m.start():]

          ret_co2emission = 'No Information'
          if len(g_ret) > 7:
              ret_co2emission = g_ret[7]

          ret_clean_flight = 'No Information'
          if ret_co2emission != 'No Information':
              value = list(ret_co2emission.split(' ')[0])[0]
              if value == 'A' or value == '+':
                  ret_clean_flight = 'False'
              elif value == '-':
                  ret_clean_flight = 'True'
          
          ret_depart_date = f'{self.date_to} {ret_depart_time}'

          row =  {
            'destination_origin': ret_origin,
            'destination_destination' : ret_destination, 
            'destination_departure_date': self.date_to,
            'destination_departure_time' : ret_depart_time,
            'destination_arrival_time': ret_arrival_time,
            'destination_airlines' : ret_airline, 
            'destination_duration' : ret_duration, 
            'destination_n_stops' : ret_stops,
            'destination_carbon_footprint' : ret_co2emission, 
            'destination_departure_datetime' : ret_depart_date,
            'price2': ret_price,
            'destination_clean_flight':ret_clean_flight,
            'ret_currency': c_symbol}

          # ?
          self.ret_list.append(row)
      return 

  def addtodf(self):
    for dict1 in self.orig_list:
      for dict2 in self.ret_list:
        row = ({**dict1 , **dict2})

        total1 = dict1['price1']
        total2 = dict2['price2']
        total = str(int(total1) + int(total2))
        del row['price1']
        del row['price2']
        row['price'] = total
        row['offset'] = 'No Information'
        del row['ret_currency']
        row['currency'] = dict2['ret_currency']
        row['carbon_footprint'] = 'No Information'
        clean_ori = dict1['origin_clean_flight']
        clean_ret = dict2['destination_clean_flight']
        del row['origin_clean_flight']
        del row['destination_clean_flight']
        clean_f = 'False'
        if clean_ori == 'True' and clean_ret == "True":
          clean_f = 'True'
        row['clean_flight'] = clean_f
        row['offer_link'] = self.query_url_complete
        row['provider_name'] = 'Google Flights'

        row['total_duration'] = self.get_total_duration(dict1['origin_duration'],dict2['destination_duration'])
        s1 = dict1['origin_n_stops']
        s2 = dict2['destination_n_stops']
        if s1 == 'Nonstop' or s1 == 'Direct':
          s1 = 0
        else:
          s1 = int(list(s1)[0])
        if s2 == 'Nonstop' or s2 == 'Direct':
          s2 = 0
        else:
          s2 = int(list(s2)[0])
        
        row['total_flights'] = int(s1+s2)
        self.df = self.df.append(row, ignore_index = True)
    return
      

  @staticmethod
  def get_total_duration(duration1 , duration2):

      h1,m1 = duration1.split('hr')
      m1 = m1.split('min')[0]

      h2,m2 = duration2.split('hr')
      m2 = m2.split('min')[0]

      m3 = int(m1) + int(m2) 
      mins = m3%60
      offset =  m3//60
      hours = int(h1) +int(h2) + int(offset)

      # Format the string with the desired format
      total_duration_str = '{} hr {} min'.format(hours, mins)
      return total_duration_str


  def convert_to_usd(self, amount, currency):
      # Create a CurrencyRates object
      cr = CurrencyRates()
      currency = self.convert_currency_name(currency)
      amount = Decimal(amount)
      usd_amount = cr.convert(currency, 'USD', amount)#, force_decimal = False)

      return usd_amount

  @staticmethod
  def convert_currency_name(currency):
    cc = CurrencyCodes()
    currency_name = cc.get_currency_name(currency)
    return currency_name

  @staticmethod
  def get_currency_name(symbol):
    currency_symbols = {
        '$': 'US Dollar',
        '€': 'Euro',
        '¥': 'Japanese Yen',
        '£': 'Pound Sterling',
        '₽': 'Russian Ruble',
        '₹': 'Indian Rupee',
        '₩': 'South Korean Won',
        'A$': 'Australian Dollar',
        'C$': 'Canadian Dollar',
        'CHF': 'Swiss Franc',
        'HK$': 'Hong Kong Dollar',
        'kr': 'Swedish Krona',
        'MX$': 'Mexican Peso',
        'S$': 'Singapore Dollar',
        'NT$': 'New Taiwan Dollar',
        'RMB': 'Chinese Yuan',
    }
    return currency_symbols[symbol]
    
  def init_scrapper(self):
    print('Looking for deals')
    result_df = self.get_df()
    return result_df