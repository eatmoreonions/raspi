#!/usr/bin/python

import os
import re
import subprocess
import time
import datetime
import httplib
import urllib
import sys

sys.path.append('/home/pi/python/Adafruit-Raspberry-Pi-Python-Code/Adafruit_BMP085')

from Adafruit_BMP085 import BMP085

# extract feed_id and api_key from environment variables
# FEED_ID = os.environ["FEED_ID"]
# API_KEY = os.environ["API_KEY"]
# DEBUG = os.environ["DEBUG"] or false

#import API_KEY from envkeys.txt
DEBUG=True


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

# main program entry point - runs continuously updating our datastreams with the
# with the current temperature, pressure, and humidity
def run():
  print "Starting environmental monitoring script"

  while True:
    bmpdata = read_bmp085()
    dhtdata = read_dht()

    if DEBUG:
      print "Updating ThingSpeak feed with temperature: %.2f F" % dhtdata['temperature']
      print "Updating ThingSpeak feed with pressure: %.2f in" % bmpdata['pressure']
      print "Updating ThingSpeak feed with humidity: %.2f percent" % dhtdata['humidity']

    params = urllib.urlencode({'field1': dhtdata['temperature'], 'field2': bmpdata['pressure'], 'field3': dhtdata['humidity']})
    headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
    conn = httplib.HTTPConnection("api.thingspeak.com:80")
    conn.request("POST", "/update?key=$API_KEY", params, headers)
    response = conn.getresponse()
    print response.status, response.reason
    data = response.read()
    conn.close()

    time.sleep(300)

run()
