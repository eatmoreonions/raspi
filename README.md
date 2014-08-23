raspi
=====

raspberry pi python projects

Dependencies
python pip
 sudo apt-get install python-pip
python twitter support
 sudo pip install python-twitter
python dropbox support
 sudo pip install dropbox


dbupload.py = simple script to upload a file to dropbox.  

dht.py = script to read the temperature and humidity from a DHT22 and output to screen

env.py = script which reads the temperature, pressure, and humidity from a DHT22 and BMP085 and updates a ThingSpeak feed

env-twitter.py = script which reads temperature, humidity, and pressure from a DHT22 and BMP085 and updates a ThingSpeak feed.  Also checks a Twitter feed for inboud direct message ("Temp", "Hum", "Press", "Upload") and replies with the temperature, humidity, pressure, or takes a picture and uploads to a DropBox account.  

env-xively.py = script which reads the temperature, pressure, and humidity from a DHT22 and BMP085 and updates a Xively feed


