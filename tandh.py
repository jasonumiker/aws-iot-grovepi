#!/usr/bin/env python
# Send Temp and Humidity to AWS IoT and display on the local screen
# By Jason Umiker
# jason.umiker@gmail.com
# Version 1.0

from grovepi import *
from grove_rgb_lcd import *
from time import sleep
from math import isnan
from datetime import date, datetime
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

HOME_PATH = '/home/pi/aws-iot-grovepi/'
ca = HOME_PATH + 'root-CA.crt'
crt = HOME_PATH + 'grovepi.cert.pem'
key = HOME_PATH + 'grovepi.private.key'
iot_endpoint = 'a12e1tnoddrce1.iot.ap-southeast-2.amazonaws.com'
thing_name = 'grovepi'

# configure sensor
dht_sensor_port = 7
dht_sensor_type = 0

# set green as backlight color
setRGB(0,255,0)

# set up AWS IoT certificate-based connection
myMQTTClient = AWSIoTMQTTClient(thing_name)
myMQTTClient.configureEndpoint(iot_endpoint, 8883)
myMQTTClient.configureCredentials(ca, key, crt)
myMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec
myMQTTClient.connect()
myMQTTClient.publish(thing_name + "/info", "connected", 0)

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
        payload = '{ "device": "' + thing_name + '","timestamp": "' + now_str + '","temperature": ' + t + ',"humidity": '+ h + ' }'
        print(payload)
        myMQTTClient.publish("tandh", payload, 0)
        
        # wait some time before re-updating the LCD and IoT
        sleep(5)

    except (IOError, TypeError) as e:
        print(str(e))
        # and since we got a type error reset the LCD's text
        setText("")
        
    except KeyboardInterrupt as e:
        print(str(e))
        # since we're exiting the program
        # it's better to leave the LCD with a blank text
        setText("")
        myMQTTClient.disconnect()
        break
