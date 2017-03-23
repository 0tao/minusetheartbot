#!/usr/bin/env python
# import the necessary packages
from socket import *
import sys
import time
import numpy as np
import imutils
import cv2
import math
from random import randint
 
# define the lower and upper boundaries of the "green"
# ball in the HSV color space, then initialize the
# list of tracked points
#lower = (40, 100, 0)
#upper = (85, 255, 255)
blower = (92, 100, 0)
bupper = (112, 255, 255)
#rlower = (0, 0, 0)
#rupper = (10, 255, 255)
#rlower = (160, 0, 0)
#rupper = (179, 255, 255)
rlower = (160, 100, 100)
rupper = (179, 255, 200)
rx, ry, bx, by = 0, 0, 1, 1

width = 800
height = 450
debug = 1

routes = [(150,100),(150,350),(550,100),(550,350)]
#routes = [(300,100),(500,100),(500,350),(300,350)]
routes = [(width/2, height/2)]
currP = [0]

camera = cv2.VideoCapture(0)
#width=int(camera.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH))
#height=int(camera.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
fourcc = cv2.cv.CV_FOURCC('m','p','4','v')
out = cv2.VideoWriter()
out.open('output.mp4', fourcc, 20, (width,height))
#if debug:
serverName = '10.209.11.115'
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))

def goTo(rx, ry, bx, by, dstx, dsty, curr):
    x = (rx+bx)/2
    y = (ry+by)/2
    dx = bx-rx
    dy = by-ry
    #cv2.circle(frame, (int(x), int(y)), int(math.sqrt((rx-bx)**2+(ry-by)**2)+rradius+bradius), (255, 255, 255), -1)
    if bx-rx != 0:
        heading = dy/dx
    else:
        heading = 100000
    #print x, y
    
    alpha = abs(math.atan(heading))
    if dx > 0:
        if dy < 0:
            alpha += 3*math.pi/2
    elif dx < 0:
        if dy > 0:
            alpha += math.pi/2
        else:
            alpha += math.pi
    else:
        if dy > 0:
            alpha = math.pi/2
        else:
            alpha = 3*math.pi/2

    if math.hypot(x - dstx, y - dsty) < 200:
        speedLimit = 50 * math.hypot(x - dstx, y - dsty) / 100
    else:
        speedLimit = 50

    if math.hypot(x - dstx, y - dsty) < 20:
        v03 = randint(-9,9)
        v12 = randint(-9,9)
        speedLimit = 30
    else:
        v03 = int((dstx-x)*math.cos(alpha)+(dsty-y)*math.sin(alpha))
        v12 = int(-(dstx-x)*math.sin(alpha)+(dsty-y)*math.cos(alpha))

    print v03, v12, speedLimit, x, y
    velocities = [-int(v03), -int(v12), int(v03), int(v12)]

    clientSocket.send(str(velocities+[int(speedLimit)]))
    stringFromServer = clientSocket.recv(1024)
    print "Server: "+stringFromServer
    print math.hypot(x - dstx, y - dsty),currP
    #if math.hypot(x - dstx, y - dsty) < 30:
    #    if curr[0]+1 < len(routes):
    #        curr[0] += 1
    #        print "+"
    #    else:
    #        curr[0] = 0


while (camera.isOpened()):


        _, frame = camera.read()

        frame = imutils.resize(frame, width=width)
 
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
                if debug:
                    rM = cv2.moments(rc)
                    rcenter = (int(rM["m10"] / rM["m00"]), int(rM["m01"] / rM["m00"]))
     
                    # only proceed if the radius meets a minimum size
                    if rradius > 0 and rradius < 50:
                            #print rradius, rx, ry
                            # draw the circle and centroid on the frame,
                            # then update the list of tracked points
                            cv2.circle(frame, (int(rx), int(ry)), int(rradius),
                                    (0, 255, 255), 2)
                            cv2.circle(frame, rcenter, int(rradius), (0, 0, 255), -1)
                bc = max(bcnts, key=cv2.contourArea)
                ((bx, by), bradius) = cv2.minEnclosingCircle(bc)
                if debug:
                    bM = cv2.moments(bc)
                    bcenter = (int(bM["m10"] / bM["m00"]), int(bM["m01"] / bM["m00"]))
     
                    # only proceed if the radius meets a minimum size
                    if bradius > 0 and bradius < 10:
                            #print bradius, bx, by
                            # draw the circle and centroid on the frame,
                            # then update the list of tracked points
                            cv2.circle(frame, (int(bx), int(by)), int(bradius),
                                    (0, 255, 255), 2)
                            cv2.circle(frame, bcenter, int(bradius), (255, 0, 0), -1)

        goTo(rx, ry, bx, by, routes[currP[0]][0], routes[currP[0]][1], currP)

        # show the frame to our screen
        cv2.imshow("Frame", frame)
        #out.write(frame)
        #cv2.imshow("Mask", mask)
        #cv2.imwrite( "frame.jpg", frame); 
        #cv2.imwrite( "rmask.jpg", rmask); 
        #cv2.imwrite( "bmask.jpg", bmask); 
        key = cv2.waitKey(1) & 0xFF

        # if the 'q' key is pressed, stop the loop
        if key == ord("q"):
                break

clientSocket.close()
camera.release()
out.release()
cv2.destroyAllWindows()
