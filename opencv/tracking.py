#!/usr/bin/env python
# import the necessary packages
import picamera
import time
import numpy as np
import imutils
import cv2
 
# define the lower and upper boundaries of the "green"
# ball in the HSV color space, then initialize the
# list of tracked points
#lower = (40, 100, 0)
#upper = (85, 255, 255)
blower = (92, 100, 0)
bupper = (112, 255, 255)
rlower = (0, 0, 0)
rupper = (10, 255, 255)

width = 800
height = 608
 
with picamera.PiCamera() as camera:
	camera.resolution = (width, height)
	camera.framerate = 24
	time.sleep(0.5)

        while True:
                frame = np.empty((height * width * 3,), dtype=np.uint8)
                camera.capture(frame, 'bgr')
                frame = frame.reshape((height, width, 3))
         
                # resize the frame, blur it, and convert it to the HSV
                # color space
                #frame = imutils.resize(frame, width=600)
                blurred = cv2.GaussianBlur(frame, (11, 11), 0)
                hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
         
                # construct a mask for the color "green", then perform
                # a series of dilations and erosions to remove any small
                # blobs left in the mask
                rmask = cv2.inRange(hsv, rlower, rupper)
                rmask = cv2.erode(rmask, None, iterations=2)
                rmask = cv2.dilate(rmask, None, iterations=2)
                bmask = cv2.inRange(hsv, blower, bupper)
                bmask = cv2.erode(bmask, None, iterations=2)
                bmask = cv2.dilate(bmask, None, iterations=2)
                
                # find contours in the mask and initialize the current
                # (x, y) center of the ball
                rcnts = cv2.findContours(rmask.copy(), cv2.RETR_EXTERNAL,
                        cv2.CHAIN_APPROX_SIMPLE)[-2]
                rcenter = None
                bcnts = cv2.findContours(bmask.copy(), cv2.RETR_EXTERNAL,
                        cv2.CHAIN_APPROX_SIMPLE)[-2]
                bcenter = None
         
                # only proceed if at least one contour was found
                if len(rcnts) > 0 and len(bcnts) > 0:
                        # find the largest contour in the mask, then use
                        # it to compute the minimum enclosing circle and
                        # centroid
                        rc = max(rcnts, key=cv2.contourArea)
                        ((rx, ry), rradius) = cv2.minEnclosingCircle(rc)
                        rM = cv2.moments(rc)
                        rcenter = (int(rM["m10"] / rM["m00"]), int(rM["m01"] / rM["m00"]))
         
                        # only proceed if the radius meets a minimum size
                        if rradius > 0 and rradius < 10:
                                print rradius, rx, ry
                                # draw the circle and centroid on the frame,
                                # then update the list of tracked points
                                cv2.circle(frame, (int(rx), int(ry)), int(rradius),
                                        (0, 255, 255), 2)
                                cv2.circle(frame, rcenter, 5, (0, 0, 255), -1)
                        bc = max(bcnts, key=cv2.contourArea)
                        ((bx, by), bradius) = cv2.minEnclosingCircle(bc)
                        bM = cv2.moments(bc)
                        bcenter = (int(bM["m10"] / bM["m00"]), int(bM["m01"] / bM["m00"]))
         
                        # only proceed if the radius meets a minimum size
                        if bradius > 0 and bradius < 10:
                                print bradius, bx, by
                                # draw the circle and centroid on the frame,
                                # then update the list of tracked points
                                cv2.circle(frame, (int(bx), int(by)), int(bradius),
                                        (0, 255, 255), 2)
                                cv2.circle(frame, bcenter, 5, (0, 0, 255), -1)
         

                # show the frame to our screen
                #cv2.imshow("Frame", frame)
                #cv2.imshow("Mask", mask)
                cv2.imwrite( "frame.jpg", frame); 
                cv2.imwrite( "rmask.jpg", rmask); 
                cv2.imwrite( "bmask.jpg", bmask); 
                key = cv2.waitKey(1) & 0xFF

                # if the 'q' key is pressed, stop the loop
                if key == ord("q"):
                        break

        #cv2.destroyAllWindows()
