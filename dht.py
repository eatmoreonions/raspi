import subprocess
import re
import time

def read_dht():
  print "reading dht temperature and humidity"

  while True:
    output = subprocess.check_output(["./Adafruit_DHT", "2302", "4"]);
    print output

  # search for humidity
    matches = re.search("Hum =\s+([0-9.]+)", output)
    if (matches):
      humidity = float(matches.group(1))
      print "Humidity:    %.1f %%" % humidity

  # search for temperature
    matches = re.search("Temp =\s+([0-9.]+)", output)
    if (matches):
      temperature = float(matches.group(1))*(9.0/5.0) + 32
      print "Temperature:    %.1f F" % temperature
      return {'temperature':temperature,'humidity':humidity}

    time.sleep(3)
