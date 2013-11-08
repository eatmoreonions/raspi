#!/usr/bin/python

import os
import re
import xively
import subprocess
import time
import datetime
import sys

sys.path.append('/home/pi/python/Adafruit-Raspberry-Pi-Python-Code/Adafruit_BMP085')

from Adafruit_BMP085 import BMP085

# extract feed_id and api_key from environment variables
# FEED_ID = os.environ["FEED_ID"]
# API_KEY = os.environ["API_KEY"]
# DEBUG = os.environ["DEBUG"] or false

#FEED_ID=1230581467
#API_KEY="3U_DsF2Cl3BdZWCCpl7fxF3f0d-SAKxvLzJIRlhUaHVVWT0g"
FEED_ID=1300283380
API_KEY="Gg8jQAZJf5xf13f843WnYspVTqiSAKx2dnRwYXhieFVGVT0g"
DEBUG=True

# initialize api client
api = xively.XivelyAPIClient(API_KEY)

# function to read temperature and pressure from bmp085
def read_bmp085():
  if DEBUG:
    print "reading bmp085 temperature and pressure"

  bmp = BMP085(0x77)
  temp = bmp.readTemperature()
  pressure = bmp.readPressure()

  temp = round(((9.0/5.0)*temp + 32), 2)
  pressure = (pressure / 100)*0.0295301
  pressure = round(pressure, 2)

  if DEBUG:
    print "bmp085 Temperature: %.2f F" % temp
    print "Pressure:    %.2f in." % pressure

  return {'temp':temp, 'pressure':pressure}

def read_dht():
  if DEBUG:
    print "reading dht temperature and humidity"

  while True:
    output = subprocess.check_output(["./Adafruit_DHT", "2302", "4"]);
    if DEBUG:
      print output

  # search for humidity 
    matches = re.search("Hum =\s+([0-9.]+)", output)
    if (matches):
      humidity = float(matches.group(1))
      if DEBUG:
        print "Humidity:    %.1f %%" % humidity

  # search for temperature 
    matches = re.search("Temp =\s+([0-9.]+)", output)
    if (matches):
      temperature = float(matches.group(1))*(9.0/5.0) + 32
      if DEBUG:
        print "Temperature:    %.1f F" % temperature
      return {'temperature':temperature,'humidity':humidity}

    time.sleep(3)


# function to return a datastream object. This either creates a new datastream,
# or returns an existing one
def get_datastream(feed):
  try:
    temp_datastream = feed.datastreams.get("temperature")
    if DEBUG:
      print "Found existing temperature datastream"
  except:
    if DEBUG:
      print "Creating new temperature datastream"
    temp_datastream = feed.datastreams.create("temperature", tags="temperature")

  try:
    pressure_datastream = feed.datastreams.get("pressure")
    if DEBUG:
      print "Found existing pressure datastream"
  except:
    if DEBUG:
      print "Creating new pressure datastream"
    pressure_datastream = feed.datastreams.create("pressure", tags="pressure")

  try:
    humidity_datastream = feed.datastreams.get("humidity")
    if DEBUG:
      print "Found existing humidity datastream"
  except:
    if DEBUG:
      print "Creating new humidity datastream"
    humidity_datastream = feed.datastreams.create("humidity", tags="humidity")

  return {'tempds':temp_datastream, 'pressureds':pressure_datastream, 'humidityds':humidity_datastream}


# main program entry point - runs continuously updating our datastreams with the
# with the current temperature, pressure, and humidity
def run():
  print "Starting environmental monitoring script"

  feed = api.feeds.get(FEED_ID)

  datastreams = get_datastream(feed)

  datastreams['tempds'].max_value = None
  datastreams['tempds'].min_value = None
  datastreams['pressureds'].max_value = None
  datastreams['pressureds'].max_value = None
  datastreams['humidityds'].min_value = None
  datastreams['humidityds'].min_value = None

  while True:
    bmpdata = read_bmp085()
    dhtdata = read_dht()

    if DEBUG:
      print "Updating Xively feed with temperature: %.2f F" % dhtdata['temperature']
      print "Updating Xively feed with pressure: %.2f in" % bmpdata['pressure']
      print "Updating Xively feed with humidity: %.2f percent" % dhtdata['humidity']

    datastreams['tempds'].current_value = dhtdata['temperature']
    datastreams['tempds'].at = datetime.datetime.utcnow()
    datastreams['tempds'].update()

    datastreams['pressureds'].current_value = bmpdata['pressure']
    datastreams['pressureds'].at = datetime.datetime.utcnow()
    datastreams['pressureds'].update()

    datastreams['humidityds'].current_value = dhtdata['humidity']
    datastreams['humidityds'].at = datetime.datetime.utcnow()
    datastreams['humidityds'].update()

    time.sleep(600)

run()
