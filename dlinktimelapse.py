#!/usr/bin/python

import urllib2
import base64
import time
from datetime import datetime

# 
# capture a series of still pictures from a dlink dcs-5020l
#

def getvars():
  delay = input("how seconds between pictures? ")
  number = input("how many pictures in the sequence? ")
  return delay, number

def takepic():
  dtn=datetime.now()
  imagename='../Pictures/dlink' + dtn.strftime("%m%d%Y-%H%M%S") + '.jpg'
  f = open(imagename, 'wb')
  request = urllib2.Request("http://10.9.5.104/image/jpeg.cgi")
  base64string = base64.encodestring('%s:%s' % ('tomc', 'tYlen0l')).replace('\n', '')
  request.add_header("Authorization", "Basic %s" % base64string)
  f.write(urllib2.urlopen(request).read())
  f.close()

def run():
  delay, number = getvars()
  
  for i in range(0, number):
    print "taking picture number " + str(i+1)
    takepic()
    time.sleep(delay)

run()
