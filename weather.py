#!/usr/bin/python

import subprocess
import re
import sys
import time
import datetime
import eeml

from Adafruit_BMP085 import BMP085


# ===========================================================================
# Cosm feed details
# ===========================================================================

API_KEY = 'KNHJree7YwgbDHx4B6u_uiiwj0qSAKxEeCtTcFZIejlwcz0g'
FEED = 117786

API_URL = '/v2/feeds/{feednum}.xml' .format(feednum = FEED)

# ===========================================================================

DEBUG = 1

while(True):
  # Initialise the BMP085 and use STANDARD mode (default value)
  # bmp = BMP085(0x77, debug=True)
  bmp = BMP085(0x77)

  # To specify a different operating mode, uncomment one of the following:
  # bmp = BMP085(0x77, 0)  # ULTRALOWPOWER Mode
  # bmp = BMP085(0x77, 1)  # STANDARD Mode
  # bmp = BMP085(0x77, 2)  # HIRES Mode
  # bmp = BMP085(0x77, 3)  # ULTRAHIRES Mode

  temp = bmp.readTemperature()
  pressure = bmp.readPressure()
  altitude = bmp.readAltitude()

  temp = (9.0/5.0)*temp + 32
  pressurehpa = (pressure / 100)
  pressure = (pressure / 100)*0.0295301
  pressure = round(pressure, 2)

  if DEBUG:
    print "bmp085 Temperature: %.2f F" % temp
    print "Pressure:    %.2f in." % pressure
    print "Pressure:    %.2f hpa" % pressurehpa
    print "Altitude:    %.2f" % altitude

  # Run the DHT program to get the humidity and temperature readings!
  output = subprocess.check_output(["./Adafruit_DHT", "2302", "4"]);
  print output
  matches = re.search("Temp =\s+([0-9.]+)", output)

  if (not matches):
    time.sleep(3)
    continue

  btemp = float(matches.group(1))
  btempF = (9.0/5.0)*btemp + 32

  # search for humidity printout
  matches = re.search("Hum =\s+([0-9.]+)", output)
  if (not matches):
        time.sleep(3)
        continue

  humidity = float(matches.group(1))

  if DEBUG:
    print "dht22 Temperature: %.1f F" % btempF
    print "Humidity:    %.1f %%" % humidity

  # ===========================================================================
  # open up cosm feed
  # ===========================================================================

  pac = eeml.Pachube(API_URL, API_KEY)

  # ===========================================================================
  # send temperature data
  # ===========================================================================
  pac.update([eeml.Data(0, temp, unit=eeml.Fahrenheit())])

  # ===========================================================================
  # send pressure data
  # ===========================================================================
  pac.update([eeml.Data(1, pressure, unit=eeml.Unit('Pressure', type='basicSI', symbol="in."))])
  # ===========================================================================
  # send humidity data
  # ===========================================================================
  pac.update([eeml.Data(2, humidity, unit=eeml.Unit('Humidity', type='basicSI', symbol="%"))])
  # ===========================================================================
  # send data to cosm
  # ===========================================================================
  pac.put()

  time.sleep(60)
