#!/usr/bin/env python
# Display Temp and Humidity on the local screen
# By Jason Umiker
# jumiker@amazon.com
# Version 1.0

from grovepi import *
from grove_rgb_lcd import *
from time import sleep
from math import isnan
from datetime import date, datetime

# configure sensor
dht_sensor_port = 7
dht_sensor_type = 0

# set green as backlight color
setRGB(0,255,0)

while True:
    try:
        # get the temperature and Humidity from the DHT sensor
        [ temp,hum ] = dht(dht_sensor_port,dht_sensor_type)
        #print("temp = "+str(temp)+"C humidity = "+str(hum)+"%")

        # check if we have nans
        # if so, then raise a type error exception
        if isnan(temp) is True or isnan(hum) is True:
            raise TypeError('nan error')

        t = str(temp)
        h = str(hum)

        # update our LCD screen with the latest data
        setText_norefresh("Temp:" + t + "C\n" + "Humidity:" + h + "%")

        # send the data up to the AWS IOT service
        now = datetime.utcnow()
        now_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        payload = '{ "timestamp": "' + now_str + '","temperature": ' + t + ',"humidity": '+ h + ' }'
        #print(payload)
        
        # wait some time before re-updating the LCD and IoT
        sleep(4)

    except (IOError, TypeError) as e:
        print(str(e))
        # and since we got a type error reset the LCD's text
        setText("")
        
    except KeyboardInterrupt as e:
        print(str(e))
        # since we're exiting the program
        # it's better to leave the LCD with a blank text
        setText("")
        break
