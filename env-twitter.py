#!/usr/bin/python

# version 3
#   added twitter command to take a pic and upload to dropbox

# version 2 
#   replaced twitter module with https://code.google.com/p/python-twitter/

import os
import re
import subprocess
import time
import datetime
import httplib
import urllib
import sys
import twitter
import dropbox
import ConfigParser

from datetime import datetime, timedelta

sys.path.append('/home/pi/python/Adafruit-Raspberry-Pi-Python-Code/Adafruit_BMP085')

from Adafruit_BMP085 import BMP085

# Dropbox API Keys
config = ConfigParser.RawConfigParser()
config.read('dbkeys.txt')

db_app_key = config.get('DropBoxKeys', 'db_app_key')
db_app_secret = config.get('DropBoxKeys', 'db_app_secret')
db_access_token = config.get('DropBoxKeys', 'db_access_token')

# Thingspeak API key
config = ConfigParser.RawConfigParser()
config.read('thingspeakkeys.txt')

API_KEY = config.get('ThingSpeakKeys', 'API_KEY')

# Twitter keys
# Twitter keys read in from twitterkeys.txt
config = ConfigParser.RawConfigParser()
config.read('twitterkeys.txt')

CONSUMER_KEY = config.get('TwitterKeys', 'CONSUMER_KEY')
CONSUMER_SECRET = config.get('TwitterKeys', 'CONSUMER_SECRET')
ACCESS_TOKEN_KEY = config.get('TwitterKeys', 'ACCESS_TOKEN_KEY')
ACCESS_TOKEN_SECRET = config.get('TwitterKeys', 'ACCESS_TOKEN_SECRET')

# Initialize lasttweet variable to one hour ago so we can alert immediately
lasttweet=datetime.now()-timedelta(hours=1)

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

def run_command(self,*args):
  p=subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  return p.communicate()

def takepic():
  newpic, error = run_command('python', '/usr/bin/sudo', '/usr/bin/raspistill', '-t', '1', '-rot', '180', '-w', '600', '-h', '600', '-o', '/home/tomc/images/still.jpg')


def tweetDirect(dmessage):
  api = twitter.Api(consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET, access_token_key=ACCESS_TOKEN_KEY, access_token_secret=ACCESS_TOKEN_SECRET)
  api.PostDirectMessage(dmessage, screen_name="eatmoreonions")
  return{}

def tweetReadDirect():
  api = twitter.Api(consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET, access_token_key=ACCESS_TOKEN_KEY, access_token_secret=ACCESS_TOKEN_SECRET)
  messages=api.GetDirectMessages()
  if messages:
    sender = str([s.sender_screen_name for s in messages])
    body =  str([s.text for s in messages])
    messid = str([s.id for s in messages])
    cleanmessid = messid.replace('[', '').replace(']', '')
    cleanbody = body.replace('[', '').replace(']', '').replace("'", "")
    cleansender = sender.replace('[', '').replace(']', '').replace("'", "")
    api.DestroyDirectMessage(cleanmessid)
    return{'sender':cleansender[1:], 'body':cleanbody[1:]}
  else:
    return{}

# main program entry point - runs continuously updating our datastreams with the
# with the current temperature, pressure, and humidity
def run():
  global lasttweet
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
    conn.request("POST", "/update?key=GRXUBE74OXFF4Z5N", params, headers)
    response = conn.getresponse()
    print response.status, response.reason
    data = response.read()
    conn.close()

#    if dhtdata['temperature'] > 90 and (datetime.now() - lasttweet) > timedelta(hours=1):
#      lasttweet=datetime.now()
#      string2tweet='Temperature is ' + repr(round(dhtdata['temperature'],1))
#      tweetDirect(string2tweet)

    time.sleep(300)
 
    inbounddirect = tweetReadDirect()
    if inbounddirect:
      dtn=datetime.now()
      datenow=dtn.strftime("%H:%M:%S %D ")
      print inbounddirect['sender'] and inbounddirect['body']
      if inbounddirect['sender'] == "eatmoreonions" and inbounddirect['body'] == "Temp":
        print("temp request message received")
        string2tweet=datenow + 'Temperature is ' + repr(round(dhtdata['temperature'],1))
        tweetDirect(string2tweet)
      elif inbounddirect['sender'] == "eatmoreonions" and inbounddirect['body'] == "Hum":
        print("humidity request message received")
        string2tweet=datenow + 'Humidty is ' + repr(round(dhtdata['humidity'],1))
        tweetDirect(string2tweet)
      elif inbounddirect['sender'] == "eatmoreonions" and inbounddirect['body'] == "Press":
        print("pressure request message received")
        string2tweet=datenow + 'Pressure is ' + repr(round(bmpdata['pressure'],1))
        tweetDirect(string2tweet)
      elif inbounddirect['sender'] == "eatmoreonions" and inbounddirect['body'] == "Upload":
        print("Picture request received")
        takepic()
        dtn=datetime.now()
        imagename='still' + dtn.strftime("%m%d%Y-%H%M%S") + '.jpg'
        flow = dropbox.client.DropboxOAuth2FlowNoRedirect(db_app_key, db_app_secret)
        client = dropbox.client.DropboxClient(db_access_token)
        f = open('/home/tomc/images/still.jpg')
        response = client.put_file(imagename, f)
        print "uploaded: ", response
        string2tweet=datenow + 'Picture uploaded'
        tweetDirect(string2tweet)
      elif inbounddirect['sender'] == "eatmoreonions" and inbounddirect['body'] == "?":
        print("Syntax request message received")
        string2tweet=datenow + 'Options are Temp  Hum  or Press'
        tweetDirect(string2tweet)


run()
