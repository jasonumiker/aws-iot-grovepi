#!/usr/bin/env python
# Send Temp and Humidity to AWS IoT and display on the local screen
# And maintain a device shadow for a LED with local button toggle
# By Jason Umiker
# jason.umiker@gmail.com
# Version 1.0

import json
from grovepi import *
from grove_rgb_lcd import *
from time import sleep
from math import isnan
from datetime import date, datetime
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient

# configure sensor
dht_sensor_port = 7
dht_sensor_type = 0

# set green as backlight color
setRGB(0,255,0)

# Custom Shadow callbacks
def custom_shadow_callback_update(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    if responseStatus == "timeout":
        print "Update request " + token + " time out!"
    if responseStatus == "accepted":
        print "Update request with token: " + token + " accepted!"
        # print(payload)
    if responseStatus == "rejected":
        print "Update request " + token + " rejected!"


def custom_shadow_callback_delta(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    print "There is a shadow delta detected"
    payload_dict = json.loads(payload)
    # print(payload)
    global LIGHTSHADOW
    LIGHTSHADOW = int(payload_dict["state"]["lighton"])
    print "Updating LIGHTSHADOW to " + str(LIGHTSHADOW) + " to resolve the delta"


# Connect the Grove LED to digital port D3
BUTTON = 8
LED = 3

# Initialize the hardware and variables
pinMode(LED, "OUTPUT")
pinMode(BUTTON, "INPUT")
BUTTONSTATE = 0
BUTTONPRESSEDCOUNT = 0
LIGHTSHADOW = 0

# set up AWS IoT certificate-based connection
myMQTTClient = AWSIoTMQTTClient("grovepi")
myMQTTClient.configureEndpoint("a12e1tnoddrce1.iot.ap-southeast-2.amazonaws.com", 8883)
myMQTTClient.configureCredentials("/home/pi/aws-iot-grovepi/root-CA.crt", 
    "/home/pi/aws-iot-grovepi/grovepi.private.key", 
    "/home/pi/aws-iot-grovepi/grovepi.cert.pem")
myMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec
myMQTTClient.connect()
myMQTTClient.publish("grovepi/info", "connected", 0)

# set up AWS IoT certificate-based connection
MY_MQTT_SHADOW_CLIENT = AWSIoTMQTTShadowClient("grovepi")
MY_MQTT_SHADOW_CLIENT.configureEndpoint(
    "a12e1tnoddrce1.iot.ap-southeast-2.amazonaws.com", 8883)
MY_MQTT_SHADOW_CLIENT.configureCredentials("/home/pi/aws-iot-grovepi/root-CA.crt", 
    "/home/pi/aws-iot-grovepi/grovepi.private.key", 
    "/home/pi/aws-iot-grovepi/grovepi.cert.pem")
MY_MQTT_SHADOW_CLIENT.configureAutoReconnectBackoffTime(1, 32, 20)
MY_MQTT_SHADOW_CLIENT.configureConnectDisconnectTimeout(10)  # 10 sec
MY_MQTT_SHADOW_CLIENT.configureMQTTOperationTimeout(5)  # 5 sec
MY_MQTT_SHADOW_CLIENT.connect()
DEVICESHADOWHANDLER = MY_MQTT_SHADOW_CLIENT.createShadowHandlerWithName(
    "grovepi", True)
DEVICESHADOWHANDLER.shadowRegisterDeltaCallback(custom_shadow_callback_delta)

print "This example will turn a LED on and off with button presses / IoT shadow deltas"
print "Connect the Button to port D" + str(BUTTON)
print "Connect the LED to the port D" + str(LED)

# do our initial report that the light is off
LASTREPORTTIME = datetime.utcnow()
print "Initial reporting LIGHTSHADOW = " + str(LIGHTSHADOW)
JSONPAYLOAD = '{"state":{"reported":{"lighton":0}}}'
DEVICESHADOWHANDLER.shadowUpdate(JSONPAYLOAD, custom_shadow_callback_update, 5)

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
        print(payload)
        myMQTTClient.publish("pi/data", payload, 0)

        # check if the button is pressed
        BUTTONSTATE = digitalRead(BUTTON)
        # if it is pressed wait for the release before toggling
        if BUTTONSTATE == 1:
            while digitalRead(BUTTON) == 1:
                BUTTONPRESSEDCOUNT = BUTTONPRESSEDCOUNT + 1

            if LIGHTSHADOW == 0:
                # LIGHTSHADOW = 1
                JSONPAYLOAD = '{"state":{"desired":{"lighton":1}}}'
                DEVICESHADOWHANDLER.shadowUpdate(
                    JSONPAYLOAD, custom_shadow_callback_update, 5)
                print "Light desired state toggled on by local switch"
            else:
                # LIGHTSHADOW = 0
                JSONPAYLOAD = '{"state":{"desired":{"lighton":0}}}'
                DEVICESHADOWHANDLER.shadowUpdate(
                    JSONPAYLOAD, custom_shadow_callback_update, 5)
                print "Light desired state toggled off by local switch"

        # change the light to reflect its local shadow
        digitalWrite(LED, LIGHTSHADOW)

        # work out the time delta between last update and now
        CURRENTTIME = datetime.utcnow()
        TIMEDELTA = CURRENTTIME - LASTREPORTTIME

        # every 2 seconds report the current state to AWS IoT
        if TIMEDELTA.seconds > 2:
            print "Reporting LIGHTSHADOW " + str(LIGHTSHADOW)
            if LIGHTSHADOW == 0:
                JSONPAYLOAD = '{"state":{"reported":{"lighton":0}}}'
            if LIGHTSHADOW == 1:
                JSONPAYLOAD = '{"state":{"reported":{"lighton":1}}}'
            DEVICESHADOWHANDLER.shadowUpdate(JSONPAYLOAD, custom_shadow_callback_update, 5)
            LASTREPORTTIME = datetime.utcnow()
        
        # wait some time before re-updating the LCD and IoT
        sleep(1)

    except (IOError, TypeError) as e:
        print(str(e))
        # and since we got a type error reset the LCD's text
        setText("")
        
    except KeyboardInterrupt as e:
        print(str(e))
        # since we're exiting the program
        # it's better to leave the LCD with a blank text
        setText("")
        digitalWrite(LED, 0)
        myMQTTClient.disconnect()
        MY_MQTT_SHADOW_CLIENT.disconnect()
        break
