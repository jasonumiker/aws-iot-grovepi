# aws-iot-grovepi
This project has two sample apps meant to be run on a Raspberry Pi with a GrovePi+ (https://www.dexterindustries.com/grovepi/) using the following add-on modules:
* Button
* LED
* Temperature / Humidity Sensor
* LCD Screen

These apps integrate the Pi with the AWS IoT Service via MQTT and the Shadow.

## Button and LED Shadow Example
In `button_light_shadow.py` the device reconciles against a cloud-based shadow representing whether the LED should be on. You can either flip this in the AWS console by editing the shadow or pushing the button which flips the shadow in the cloud which then reconciles down to the device.

## Temperature and Humidity
In `tandh.py` the device takes temperature and humidity readings and displays them on the LCD screen as well as emits them via MQTT to the IoT service. These can then be published to S3, ElasticSearch or DynamoDB as required via rules in the AWS IoT Service.
