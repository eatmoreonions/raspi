#!/usr/bin/python

# version 7
#   added upload to wunderground pws site and turned DHT22 back on for humidity
# version 6
#   moved to picamera python library
# version 5
#   included variable for twitter SENDER
# version 4
#   DHT has become unreliable - switched to BMP for temp measurement

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
import picamera
import twitter
import dropbox
import Adafruit_DHT
import ConfigParser
from datetime import datetime, timedelta
import Adafruit_BMP.BMP085 as BMP085

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

# Wunderground pws station id and password
config = ConfigParser.RawConfigParser()
config.read('wunderground.txt')
pwsstationid = config.get('PWS', 'stationid')
pwspassword = config.get('PWS', 'password')

# Twitter keys
# Twitter keys read in from twitterkeys.txt
config = ConfigParser.RawConfigParser()
config.read('twitterkeys.txt')
CONSUMER_KEY = config.get('TwitterKeys', 'CONSUMER_KEY')
CONSUMER_SECRET = config.get('TwitterKeys', 'CONSUMER_SECRET')
ACCESS_TOKEN_KEY = config.get('TwitterKeys', 'ACCESS_TOKEN_KEY')
ACCESS_TOKEN_SECRET = config.get('TwitterKeys', 'ACCESS_TOKEN_SECRET')
SENDER = config.get('TwitterKeys', 'SENDER')

# Initialize lasttweet variable to one hour ago so we can alert immediately
lasttweet=datetime.now()-timedelta(hours=1)

DEBUG=True


# function to read temperature and pressure from bmp085
def read_bmp085():
  if DEBUG:
    print "reading bmp085 temperature and pressure"

  bmp = BMP085.BMP085()
  temp = bmp.read_temperature()
  pressure = bmp.read_pressure()
  if DEBUG:
    print "Temperature: %.2f C" % temp
    print "Pressure:    %.2f hPa" % pressure

  temp = round(((9.0/5.0)*temp + 32), 2)
  pressure = (pressure / 100)*0.0295301
  pressure = round(pressure, 2)
  if DEBUG:
    print "Temperature: %.2f F" % temp
    print "Pressure:    %.2f in." % pressure

  return {'temp':temp, 'pressure':pressure}

def read_dht():
  if DEBUG:
    print "reading dht temperature and humidity"
  dhthumidity, dhttemp = Adafruit_DHT.read_retry(22, 4)
  if dhthumidity is not None and dhttemp is not None:
    print 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(dhttemp, dhthumidity)
    return {'dhttemp':dhttemp, 'dhthumidity':dhthumidity}
  else:
    return {'dhttemp':0, 'dhthumidity':0}


def takepic():
  with picamera.PiCamera() as cam:
    cam.resolution = (600, 600)
    cam.capture('/home/tomc/images/still.jpg')

def tweetDirect(dmessage):
  api = twitter.Api(consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET, access_token_key=ACCESS_TOKEN_KEY, access_token_secret=ACCESS_TOKEN_SECRET)
  api.PostDirectMessage(dmessage, screen_name=SENDER)
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
      print "Updating ThingSpeak feed with temperature: %.2f F" % bmpdata['temp']
      print "Updating ThingSpeak feed with pressure: %.2f in" % bmpdata['pressure']
      print "Updating ThingSpeak feed with humidity: %.2f percent" % dhtdata['dhthumidity']

    params = urllib.urlencode({'field1': bmpdata['temp'], 'field2': bmpdata['pressure'], 'field3': dhtdata['dhthumidity']})
    headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
    conn = httplib.HTTPConnection("api.thingspeak.com:80")
    conn.request("POST", "/update?key=GRXUBE74OXFF4Z5N", params, headers)
    response = conn.getresponse()
    print response.status, response.reason
    data = response.read()
    conn.close()
###
    print "sending to wunderground"
    try:
      conn = httplib.HTTPConnection("weatherstation.wunderground.com")
      path = "/weatherstation/updateweatherstation.php?ID=" + pwsstationid + "&PASSWORD=" + pwspassword + "&dateutc=now" + "&tempf=" + str(bmpdata['temp']) + "&baromin=" + str(bmpdata['pressure']) + "&humidity=" + str(dhtdata['dhthumidity']) + "&softwaretype=RaspberryPi&action=updateraw"
      print path
      conn.request("GET", path)
      res = conn.getresponse()
      print res.status
      # checks whether there was a successful connection (HTTP code 200 and content of page contains "success")
      if ((int(res.status) == 200) & ("success" in res.read())):
        print "%s - Successful Upload to Wunderground\n" % str(datetime.now())
      else:
        print "%s -- Upload not successful, check username, password, and formating..." % (str(datetime.now()))
    except IOError as e: #in case of any kind of socket error
      print "{0} -- I/O error({1}): {2}".format(datetime.now(), e.errno, e.strerror)


###
    time.sleep(300)
 
    inbounddirect = tweetReadDirect()
    if inbounddirect:
      dtn=datetime.now()
      datenow=dtn.strftime("%H:%M:%S %D ")
      print inbounddirect['sender'] and inbounddirect['body']
      if inbounddirect['sender'] == SENDER and inbounddirect['body'] == "Temp":
        print("temp request message received")
        string2tweet=datenow + 'Temperature is ' + repr(round(bmpdata['temp'],1))
        tweetDirect(string2tweet)
      elif inbounddirect['sender'] == SENDER and inbounddirect['body'] == "Hum":
        print("humidity request message received")
        string2tweet=datenow + 'Humidty is ' + repr(round(dhtdata['humidity'],1))
        tweetDirect(string2tweet)
      elif inbounddirect['sender'] == SENDER and inbounddirect['body'] == "Press":
        print("pressure request message received")
        string2tweet=datenow + 'Pressure is ' + repr(round(bmpdata['pressure'],1))
        tweetDirect(string2tweet)
      elif inbounddirect['sender'] == SENDER and inbounddirect['body'] == "Upload":
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
      elif inbounddirect['sender'] == SENDER and inbounddirect['body'] == "?":
        print("Syntax request message received")
        string2tweet=datenow + 'Options are Temp  Hum  Press or Upload'
        tweetDirect(string2tweet)


run()
