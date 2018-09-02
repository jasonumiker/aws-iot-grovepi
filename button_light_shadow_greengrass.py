#!/usr/bin/env python
# Example app to control an LED from AWS Greengrass Device Shadow
# There is a local button that will also toggle the desired state
# By Jason Umiker
# Version 1.0

import json
import datetime
import uuid
from grovepi import *
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from AWSIoTPythonSDK.core.greengrass.discovery.providers import DiscoveryInfoProvider

HOME_PATH = '/home/pi/aws-iot-grovepi/'
ca = HOME_PATH + 'root-CA.crt'
crt = HOME_PATH + '8f3c6c9ca7.cert.pem'
key = HOME_PATH + '8f3c6c9ca7.private.key'
iot_endpoint = 'a12e1tnoddrce1.iot.ap-southeast-2.amazonaws.com'
core_arn = 'arn:aws:iot:ap-southeast-2:505070718513:thing/Greengrass_Core'

# Custom Shadow callbacks
def custom_shadow_callback_update(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    if responseStatus == "timeout":
        print "Update request " + token + " time out!"
    if responseStatus == "accepted":
        print "Update request with token: " + token + " accepted!"
        print(payload)
    if responseStatus == "rejected":
        print "Update request " + token + " rejected!"


def custom_shadow_callback_delta(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    print "There is a shadow delta detected"
    payload_dict = json.loads(payload)
    print(payload)
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

# Discover the Core
diProvider = DiscoveryInfoProvider()
diProvider.configureEndpoint(iot_endpoint)
diProvider.configureCredentials(ca, crt, key)
diProvider.configureTimeout(10)
discoveryInfo = diProvider.discover('Greengrass_Core')
infoObj = discoveryInfo.toObjectAtGroupLevel()
groupId = list(infoObj.keys())[0]
group = infoObj[groupId]
core = group.getCoreConnectivityInfo(core_arn)
#for addr in core.connectivityInfoList:
#    print addr.host
connectivityInfo = core.connectivityInfoList[0]

#Get groupCA
caList = discoveryInfo.getAllCas()
_, ca_crt = caList[0]
group_ca_path = '%s%s_CA_%s.crt' % (HOME_PATH, groupId, str(uuid.uuid4()))
with open(group_ca_path, 'w') as group_ca_file:
    group_ca_file.write(ca_crt)

# set up AWS IoT certificate-based connection
MY_MQTT_SHADOW_CLIENT = AWSIoTMQTTShadowClient("grovepi_greengrass")
MY_MQTT_SHADOW_CLIENT.configureEndpoint(connectivityInfo.host, connectivityInfo.port)
MY_MQTT_SHADOW_CLIENT.configureCredentials(group_ca_path, key, crt)
MY_MQTT_SHADOW_CLIENT.configureAutoReconnectBackoffTime(1, 32, 20)
MY_MQTT_SHADOW_CLIENT.configureConnectDisconnectTimeout(10)  # 10 sec
MY_MQTT_SHADOW_CLIENT.configureMQTTOperationTimeout(5)  # 5 sec
MY_MQTT_SHADOW_CLIENT.connect()
DEVICESHADOWHANDLER = MY_MQTT_SHADOW_CLIENT.createShadowHandlerWithName(
    "grovepi_greengrass", True)
DEVICESHADOWHANDLER.shadowRegisterDeltaCallback(custom_shadow_callback_delta)

print "This example will turn a LED on and off with button presses / IoT shadow deltas"
print "Connect the Button to port D" + str(BUTTON)
print "Connect the LED to the port D" + str(LED)

# do our initial report that the light is off
LASTREPORTTIME = datetime.datetime.utcnow()
print "Initial reporting LIGHTSHADOW = " + str(LIGHTSHADOW)
JSONPAYLOAD = '{"state":{"reported":{"lighton":0}}}'
DEVICESHADOWHANDLER.shadowUpdate(JSONPAYLOAD, custom_shadow_callback_update, 5)

while True:
    try:
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
        CURRENTTIME = datetime.datetime.utcnow()
        TIMEDELTA = CURRENTTIME - LASTREPORTTIME

        # every 2 seconds report the current state to AWS IoT
        if TIMEDELTA.seconds > 2:
            print "Reporting LIGHTSHADOW " + str(LIGHTSHADOW)
            if LIGHTSHADOW == 0:
                JSONPAYLOAD = '{"state":{"reported":{"lighton":0}}}'
            if LIGHTSHADOW == 1:
                JSONPAYLOAD = '{"state":{"reported":{"lighton":1}}}'
            DEVICESHADOWHANDLER.shadowUpdate(JSONPAYLOAD, custom_shadow_callback_update, 5)
            LASTREPORTTIME = datetime.datetime.utcnow()

    except KeyboardInterrupt:
        digitalWrite(LED, 0)
        break
    except IOError:
        print "Error"
