#!/usr/bin/python

# Version 5
#   read in twitter keys from config file

# Version 4
#   added light sensor

# Version 3
#   added tweet for last motion 

# Version 2
#   moved to new twitter module

import RPi.GPIO as io
import os
import re
import subprocess
import time
import datetime
import httplib
import urllib
import sys
import twitter
from datetime import datetime, timedelta
import ConfigParser

io.setmode(io.BCM)
pir_pin = 18
lightsensor_pin = 23
lightthreshhold = 200
bufsize = 0

i = 0
c = 0

# Twitter keys read in from twitterkeys.txt
config = ConfigParser.RawConfigParser()
config.read('twitterkeys.txt')

CONSUMER_KEY = config.get('TwitterKeys', 'CONSUMER_KEY')
CONSUMER_SECRET = config.get('TwitterKeys', 'CONSUMER_SECRET')
ACCESS_TOKEN_KEY = config.get('TwitterKeys', 'ACCESS_TOKEN_KEY')
ACCESS_TOKEN_SECRET = config.get('TwitterKeys', 'ACCESS_TOKEN_SECRET')

# Initialize lasttweet variable to one hour ago so we can alert immediately
lasttweet=datetime.now()-timedelta(hours=1)

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

def readlightlevel():
    reading = 0
    io.setup(lightsensor_pin, io.OUT)
    io.output(lightsensor_pin, io.LOW)
    time.sleep(0.1)

    io.setup(lightsensor_pin, io.IN)
    # This takes about 1 millisecond per loop cycle
    while (io.input(lightsensor_pin) == io.LOW):
            reading += 1
    return reading
 
io.setup(pir_pin, io.IN)

# sleep for 60 seconds to not alert on my own movement
time.sleep(60)

# determine current light level to so we can trigger on transition
if readlightlevel() < lightthreshhold:
    ll = 1
    print "the light is on"
else: 
    ll = 0
    print "the light is off"
 
while True:
    print("checking alarm...")
    if io.input(pir_pin):
        f=open('lastmotion', 'w', bufsize)
#        f.write(str(datetime.now()))
        f.write(time.strftime('%X %x %Z'))
        f.closed
    if io.input(pir_pin) and (datetime.now() - lasttweet) > timedelta(minutes=30):
        lasttweet=datetime.now()
        lasttweetreadable = time.strftime('%X %x %Z')
        string2tweet='motion alert ' + lasttweetreadable
        print string2tweet
#        tweetDirect(string2tweet)

# only check the light level every minute or so...
    c += 1
    if c  == 4:
        c = 0
        print("checking light level")
        lightlevel = readlightlevel()

        if lightlevel < lightthreshhold and ll == 0: 
            print "just transitioned from dark to light" + str(lightlevel)
            ll = 1
            l=open('lastlighton', 'w', bufsize)
            l.write(time.strftime('%X %x %Z'))
            l.closed

        if lightlevel > lightthreshhold and ll == 1: 
            print "just transitioned from light to dark" + str(lightlevel)
            ll = 0
            l=open('lastlightoff', 'w', bufsize)
#            l.write(str(datetime.now()))
            l.write(time.strftime('%X %x %Z'))
            l.closed

# need to check for motion every 16 seconds in order to not miss something
    time.sleep(16)

# only check for twitter messages every minute or so... 
    i += 1
    if i == 4:
        indirect = tweetReadDirect()
        if indirect:
          print indirect['sender'] and indirect['body']
          if indirect['sender'] == "eatmoreonions" and indirect['body'] == "Enditall":
            print("terminate message received")
            break
          if indirect['sender'] == "eatmoreonions" and indirect['body'] == "Lastmotion":
            f=open('lastmotion', 'r')
            string2tweet='last motion was seen in the office at ' + f.read() 
            print string2tweet
            tweetDirect(string2tweet)
            f.closed
          if indirect['sender'] == "eatmoreonions" and indirect['body'] == "Lightonat":
            currenttime = time.strftime('%X %x %Z')
            lstatus=open('lastlighton', 'r')
            string2tweet='Currently it is ' + currenttime + ' The last time the office transitioned from dark to light was at ' + lstatus.read() 
            print string2tweet
            tweetDirect(string2tweet)
            lstatus.closed
          if indirect['sender'] == "eatmoreonions" and indirect['body'] == "Lightoffat":
            currenttime = time.strftime('%X %x %Z')
            lstatus=open('lastlightoff', 'r')
            string2tweet='Currently it is ' + currenttime + ' The last time the office transitioned from light to dark was at ' + lstatus.read() 
            print string2tweet
            tweetDirect(string2tweet)
            lstatus.closed
          if indirect['sender'] == "eatmoreonions" and indirect['body'] == "?":
            currenttime = time.strftime('%X %x %Z')
            string2tweet= currenttime + ': Options are: Lightoffat, Lightonat, Lastmotion' 
            print string2tweet
            tweetDirect(string2tweet)
        i = 0

