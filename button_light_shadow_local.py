#!/usr/bin/env python
# Example app to control an LED via local button
# By Jason Umiker
# Version 1.0

import time
from grovepi import *

# Connect the Grove LED to digital port D3
button = 8
led = 3 

# Initialize the hardware and variables
pinMode(led,"OUTPUT")
pinMode(button,"INPUT")
buttonState = 0
buttonPressedCount = 0
lightShadow = 0

print ("This example will turn a LED on and off with button presses")
print ("Connect the Button to port D8")
print ("Connect the LED to the port D3" )

while True:
    try:
        # check if the button is pressed
	buttonState = digitalRead(button);
        # if it is pressed wait for the release before toggling
	if (buttonState == 1):
		while (digitalRead(button) == 1):
			buttonPressedCount = buttonPressedCount + 1
			
		if (lightShadow == 0):
			lightShadow = 1
			print ("Light toggled on")
		else:
			lightShadow = 0
			print ("Light toggled off")
	
	# change the light to reflect its shadow
	digitalWrite(led,lightShadow)

	#print(str(buttonState)+","+str(lightShadow))

	buttonPressedCount = 0

    except KeyboardInterrupt:	# Turn LED off before stopping
        digitalWrite(led,0)
        break
    except IOError:				# Print "Error" if communication error encountered
        print ("Error")
