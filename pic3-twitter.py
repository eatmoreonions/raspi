#!/usr/bin/python

# version 6
#   code cleanup
# version 5
#   updated dropbox api to v2
# version 4
#   switched to picamera python interface
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
import picamera

from datetime import datetime, timedelta

# Dropbox API Keys
config = ConfigParser.RawConfigParser()
config.read('dbkeys.txt')

#db_app_key = config.get('DropBoxKeys', 'db_app_key')
#db_app_secret = config.get('DropBoxKeys', 'db_app_secret')
db_access_token = config.get('DropBoxKeys', 'db_access_token')


# Twitter keys
# Twitter keys read in from twitterkeys.txt
config = ConfigParser.RawConfigParser()
config.read('twitterkeys.txt')

CONSUMER_KEY = config.get('TwitterKeys', 'CONSUMER_KEY')
CONSUMER_SECRET = config.get('TwitterKeys', 'CONSUMER_SECRET')
ACCESS_TOKEN_KEY = config.get('TwitterKeys', 'ACCESS_TOKEN_KEY')
ACCESS_TOKEN_SECRET = config.get('TwitterKeys', 'ACCESS_TOKEN_SECRET')
SENDER = config.get('TwitterKeys', 'SENDER')

PICSAVELOCATION='/home/tomc/Pictures/still.jpg'

DEBUG=True

# Initialize lasttweet variable to one hour ago so we can alert immediately
lasttweet=datetime.now()-timedelta(hours=1)

def takepic():
  camera = picamera.PiCamera()
  camera.capture(PICSAVELOCATION)
  camera.close()

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
    cleanmessid = messid.replace('[', '').replace(']', '').replace('L', '')
    cleanbody = body.replace('[', '').replace(']', '').replace("'", "")
    cleansender = sender.replace('[', '').replace(']', '').replace("'", "")
    api.DestroyDirectMessage(int(cleanmessid))
    return{'sender':cleansender[1:], 'body':cleanbody[1:]}
  else:
    return{}

# main program entry point - runs continuously checking twitter for direct messages
# with with command to upload picture to dropbox
def run():
  global lasttweet
  if DEBUG: print "Starting twitter monitoring"

  while True:
    inbounddirect = tweetReadDirect()
    if inbounddirect:
      dtn=datetime.now()
      datenow=dtn.strftime("%H:%M:%S %D ")
      if DEBUG: print inbounddirect['sender'] and inbounddirect['body']

      if inbounddirect['sender'] == SENDER and inbounddirect['body'] == "Upload":
        if DEBUG: print("Picture request received")
        takepic()
        dtn=datetime.now()
        imagename='/still' + dtn.strftime("%m%d%Y-%H%M%S") + '.jpg'

        client = dropbox.Dropbox(db_access_token)
        f = open(PICSAVELOCATION)
        data = f.read()
        uploadstatus = client.files_upload(data, imagename)
        if DEBUG: print uploadstatus

        string2tweet=datenow + 'Picture uploaded'
        tweetDirect(string2tweet)

      elif inbounddirect['sender'] == SENDER and inbounddirect['body'] == "?":
        if DEBUG: print("Syntax request message received")
        string2tweet=datenow + 'To upload picture send Upload'
        tweetDirect(string2tweet)

    time.sleep(300)

run()
