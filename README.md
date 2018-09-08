# aws-iot-grovepi
This Workshop has two sample apps meant to be run on a Raspberry Pi with a GrovePi+ (https://www.dexterindustries.com/grovepi/) using the following add-on modules:
* Button
* LED
* Temperature / Humidity Sensor
* LCD Screen

These apps integrate the Pi with the AWS IoT Service via MQTT and the Shadow. Once the data is in S3 we do some analytics with our serverless Data Lake services.

## Workshop

### Step 1 - Add our Thing to the IoT Core Service
1. Choose the `Sydney` Region in the upper right of the AWS Console
1. Open the `IoT Core` Service
1. On the left-hand side choose `Manage` -> `Things`
1. Click the `Register a thing` button
1. Click the `Create a single thing` button
1. Enter `username-grovepi` for the thing's name where username is your unique username then click `Next`
1. Click the `Create certificate` button to the right of `One-click certificate creation`
1. Click the `Download` links next to all three certificates generated for the new Thing
1. Click `Done`

### Step 2 - Add a Policy to the new Certificate and Activate Access
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

At this stage we now have everything ready to go in the Cloud. Now we'll set up our IoT Device.

### Step 3 - Set up our Rasperry Pi + GrovePI device
1. Open a Terminal (should default to `/home/pi` folder)
1. Clone the GitHub repo with the command `git clone https://github.com/jasonumiker/aws-iot-grovepi.git`
1. Run the command `cd aws-iot-grovepi`
1. Run the command `./download_root_ca.sh` to download the root-CA.crt file
1. Put the three certificate files downloaded from the Thing creation into this folder
1. Connect the Button to D8
1. Connect the LED to D3
1. Connect the Temperature and Humidity Sensor to D7
1. Connect the LCD screen to any of the I2C ports

### Step 4 - button_light_shadow.py Example
This example illustrates IoT Core's shadow feature.

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

The shadow allows you to manage IoT Things that have inconsistent network connectivity by setting the Desired state in the cloud - the device will reconcile with that state when it reconnects to the network. It also lets you see the current Actual state of devices in the field if they are reporting back properly.

If you want to allow for local non-Cloud logic and processing for Things in areas where the network connectivity is unreliable or there is a large fleet of Things and them all reaching out to the Cloud is inefficient AWS Greengrass can help. It allows local on-site shadows and Lambdas to process the data and perhaps only send the relevant subset or aggregations back up to the Cloud.

### Step 5 - tandh.py Example
This example illustrates one of the most common use-cases - IoT Sensors sending data back for analytics in the Cloud.

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
This example illustrates how the IoT Core's Rules work as well as how to collect IoT data into a Data Lake in S3.

1. Go to the S3 Console and click `+ Create bucket`
1. For bucket name use `username-tandh-raw` e.g. jumiker-tandh-raw (this name needs to be globally unique)
1. Click `Create`
1. Go to the IoT Core Console
1. On the left-hand side go to `Act` then click `Create rule`
1. Enter `tandh_datalake_raw` for the `Name`
1. Enter `*` for the `Attribute`
1. Enter `tandh` for the `Topic filter`
1. Click `Add action` button
1. Click `Store messages in an Amazon S3 bucket` and then the `Configure action` button
1. Select the new S3 bucket from the `S3 bucket` drop-down
1. Enter `${timestamp()}` for the `Key`
1. Click `Create a new role`
1. Enter `tandh-datalake-raw-rule` for the `IAM role name` and then click the `Create a new role` button
1. Choose the new role from the drop-down and then click the `Add action` button
1. Click the `Create rule` button

### Step 7 - Analyse the raw data in Athena
This example shows how to analyse the data in S3 without needing to load it into a database or Elasticsearch first.

1. Go to the Glue Console and choose `Crawlers` on the left-hand side
1. Click the `Add crawler` button
1. Enter `username-tandh` for the `Crawler name` and click `Next`
1. Click the folder icon to the right of the `Include path` and choose the tandh bucket then click `Select`
1. Click `Next` and `Next` again
1. Leave the default option to `Create an IAM role` and enter `tandh` for the IAM role name then click `Next`
1. Leave the default `Frequency` of `Run on demand` and click `Next`
1. Click `Add database`, enter `username-tandh` for the name, and click `Create`
1. Click `Next` and then `Finish`
1. Do an initial run of the new Crawler
1. After that succeeds go to the Athena service in the Console
1. Choose the new `username-tandh` database in the dropdown
1. Note the table name on the left-hand side which should correspond to the bucket name
1. Run a query like `SELECT * from username_tandh_raw;` substituting in your own table name.
1. (Optional) Try other SQL queries and aggregations

### Step 8 - Visualise the data in QuickSight
This example shows how we can visualise the SQL queries that we are making against the data in S3 via Athena.

1. Go to the QuickSight Console ensuring you select N. Virginia for the region
1. Click the User icon in the upper-right and choose `Manage QuickSight`
1. Choose `Account Settings` on the left-hand side
1. Click the `Edit AWS permissions` button
1. Tick `Athena` and `S3` and then click the `Choose S3 buckets` link and choose the tandh_raw bucket
1. Click the `Apply` button and then change the region back to `Sydney`
1. Click the `Manage data` button in the upper-right
1. Click the `New data set` button in the upper-left
1. Click on `Athena`
1. Enter `username-tandh` for the `Data source name` substituting your own name or username
1. Click on the `Create data source` button
1. Pick your new Database and Table from the dropdowns then click the `Select` button
1. Tick `Directly query your data` then click the `Visualize` button
1. In the `Fields list` click `Timestamp` then `Temperature` then `Humidity`
1. Under `Visual types` click the `Line chart`

### (Optional) Step 9 - Play around with the SDKs and other GrovePi sensors/devices
1. There is a number of SDKs for the other sensors/devices in the box in the `/home/pi/Dexter/GrovePi/Software/` folder.
    1. The Python one seems to be the most fully-formed
1. And to integrate these things with the cloud our IoT SDKs are here - https://docs.aws.amazon.com/iot/latest/developerguide/iot-sdks.html
1. We'll reset the SD Card after the workshop so feel free to download and do whatever you like on the device for the rest of the session