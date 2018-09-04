# aws-iot-grovepi
This project has two sample apps meant to be run on a Raspberry Pi with a GrovePi+ (https://www.dexterindustries.com/grovepi/) using the following add-on modules:
* Button
* LED
* Temperature / Humidity Sensor
* LCD Screen

These apps integrate the Pi with the AWS IoT Service via MQTT and the Shadow.

## Button and LED Shadow Example
In `button_light_shadow.py` the device reconciles against a cloud-based shadow representing whether the LED should be on. You can either flip this in the AWS console by editing the shadow or pushing the button which flips the shadow in the cloud which then reconciles down to the device.

Whereas `button_light_shadow_greengrass.py` reconciles against a Greengrass-based local shadow instead of one directly in the Cloud.

And `button_light_shadow_local.py` is a local test that does not interact with the Cloud at all.

## Temperature and Humidity
In `tandh.py` the device takes temperature and humidity readings and displays them on the LCD screen as well as emits them via MQTT to the IoT service. These can then be published to S3, ElasticSearch or DynamoDB as required via rules in the AWS IoT Service.

And `tandh_local.py` is a local test that does not interact with the Cloud at all.

## Workshop

### Step 1 - Add our Thing to the IoT Core Service
<details>
  <summary>
    Show details
  </summary>
  1. Choose the `Sydney` Region in the upper right of the AWS Console
  1. Open the `IoT Core` Service
  1. On the left-hand side choose `Manage` -> `Things`
  1. Click the `Register a thing` button
  1. Click the `Create a single thing` button
  1. Enter `grovepi` for the thing's name then click `Next`
  1. Click the `Create certificate` button to the right of `One-click certificate creation`
  1. Click the `Download` links next to all three certificates generated for the new Thing
  1. Click `Done`
</details>

### Step 2 - Add a Policy to the new Certificate and Activate
1. On the left-hand side go to `Secure` -> `Policies`
1. Click the `Create a policy` button
1. Enter `grovepi` for the policy's name
1. Enter `iot:*` for the `Action`
1. Enter `*` for the `Resource`
1. Tick `Allow` and then click `Create`
1. On the left-hand side go to `Manage` -> `Things` and click on `grovepi`
1. On the left-hand side go to `Security`
1. On the left-hand side go to Policies
1. Click `Actions` in the upper right corner and choose `Attach policy`
1. Tick the `grovepi` Policy and then click `Attach`
1. Click `Actions` in the upper right corner and choose `Activate`
1. Click the `Activate` button

### Step 3 - Set up our GrovePI device
1. Open a Terminal (should default to `/home/pi` folder)
1. Clone the GitHub repo with the command `git clone https://github.com/jasonumiker/aws-iot-grovepi.git`
1. Run the command `cd aws-iot-grovepi`
1. Run the command `./download_root_ca.sh` to download the root-CA.crt file
1. Put the three certificate files downloaded from the Thing creation into this folder
1. Connect the Button to D8
1. Connect the LED to D3
1. Connect the Temperature and Humidity Sensor to D7
1. Connect the LCD screen to any of the I2C ports

### Step 4 - button_light_shadow.py
1. Edit `button_light_shadow.py` and update the following variables near the top:
    1. crt to `xxxxxxxxxx-certificate.pem.crt`
    1. key to `xxxxxxxxxx-private.pem.key`
    1. iot_endpoint to the `Endpoint` listed under `Settings` on the left-hand side of the IoT Core Console
1. Run `./button_light_shadow.py`
1. Try clicking the button and watching the LED change
1. Go to `Manage` then `Things` on the left-hand side of the IoT Core Console
1. Click on the `grovepi` Thing
1. Click `Shadow` on the left-hand side
1. Click the button and watch the Shadow document change
1. Click the `Edit` link in the upper right of the Shadow document
1. Change the document's Desired to 1 if it's 0 or 0 if it's 1 and `Save`
1. Note the split-second `Delta` field that is added to the document to identify that there is a delta between the desired state in the cloud and the actual state on the device. The device subscribes to deltas and will change to match within a few seconds.

### Step 5 - tandh.py
1. Edit `tandh.py` and update the following variables near the top:
    1. crt to `xxxxxxxxxx-certificate.pem.crt`
    1. key to `xxxxxxxxxx-private.pem.key`
    1. iot_endpoint to the `Endpoint` listed under `Settings` on the left-hand side of the IoT Core Console
1. Run `./tandh.py`
1. Note that the Temperature and Humidity values are displayed on the LCD
1. See that they are also sent to the IoT service via MQTT:
    1. Go to `Test` on the left-hand side of the Iot Core Service Console
    1. Under `Subscription topic` type `tandh` and click `Subscribe to topic`
    1. Note that every few seconds the Thing is sending data to the Cloud about the Temperature and Humidity
    
### Step 6 - Rule to store incoming TanH raw data from MQTT in an S3 bucket
1. Go to the S3 Console and click `+ Create bucket`
1. For bucket name use `[your name]-tandh-raw` e.g. jumiker-tandh-raw (this name needs to be globally unique)
1. Click `Create`
1. Go to the IoT Core Console
1. On the left-hand side go to `Act` then click `Create rule`
1. Enter `tandh_datalake_raw` for the `Name`
1. Enter `*` for the `Attribute`
1. Enter `tandh` for the `Topic filter`
1. Click `Add action` button
1. Click `Store messages in an Amazon S3 bucket` and then the `Configure action` button
1. Select the new S3 bucket from the `S3 bucket` drop-down
1. Enter `tandh-raw` for the `Key`
1. Click `Create a new role`
1. Enter `tandh-datalake-raw-rule` for the `IAM role name` and then click the `Create a new role` button
1. Choose the new role from the drop-down and then click the `Add action` button
1. Click the `Create rule` button