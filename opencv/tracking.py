#!/usr/bin/env python
# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import numpy as np
import imutils
import cv2
 
# define the lower and upper boundaries of the "green"
# ball in the HSV color space, then initialize the
# list of tracked points
greenLower = (0, 50, 0)
greenUpper = (30, 150, 60)
#greenLower = (10, 20, 100)
#greenUpper = (60, 70, 180)
 
camera = PiCamera()
camera.resolution = (1296, 972)
camera.framerate = 24
rawCapture = PiRGBArray(camera, size=(1296, 972))

time.sleep(0.1)
 
# keep looping
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        frame = frame.array
 
	# resize the frame, blur it, and convert it to the HSV
	# color space
	#frame = imutils.resize(frame, width=600)
	#blurred = cv2.GaussianBlur(frame, (11, 11), 0)
	#frame = cv2.GaussianBlur(frame, (11, 11), 0)
	#hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
 
	# construct a mask for the color "green", then perform
	# a series of dilations and erosions to remove any small
	# blobs left in the mask
	#mask = cv2.inRange(hsv, greenLower, greenUpper)
	mask = cv2.inRange(frame, greenLower, greenUpper)
	mask = cv2.erode(mask, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=2)
        
	# find contours in the mask and initialize the current
	# (x, y) center of the ball
	cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)[-2]
	center = None
 
	# only proceed if at least one contour was found
	if len(cnts) > 0:
		# find the largest contour in the mask, then use
		# it to compute the minimum enclosing circle and
		# centroid
		c = max(cnts, key=cv2.contourArea)
                ((x, y), radius) = cv2.minEnclosingCircle(c)
		M = cv2.moments(c)
		center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
 
		# only proceed if the radius meets a minimum size
		if radius > 0 and radius < 10:
                        print radius, x, y
			# draw the circle and centroid on the frame,
			# then update the list of tracked points
			cv2.circle(frame, (int(x), int(y)), int(radius),
				(0, 255, 255), 2)
			cv2.circle(frame, center, 5, (0, 0, 255), -1)
 

	# show the frame to our screen
	#cv2.imshow("Frame", frame)
	#cv2.imshow("Mask", mask)
	key = cv2.waitKey(1) & 0xFF

        rawCapture.truncate(0)
 
	# if the 'q' key is pressed, stop the loop
	if key == ord("q"):
		break

#cv2.destroyAllWindows()
