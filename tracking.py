#!/usr/bin/env python
# import the necessary packages
import sys
import time
import math     # math.pi, math.sin, math.cos
import argparse # argparse
from socket import *
from random import randint
try:
    import numpy as np
    import imutils
    import cv2
except ImportError as error:
    print "ImportError:", error.args[0]
    sys.exit(1)

__author__      = 'Jack B. Du (Jiadong Du)'
__email__       = 'jackbdu@nyu.edu'
__copyright__   = 'Copyright 2017, Jack B. Du (Jiadong Du)'
__license__     = 'Apache-2.0'
__status__      = 'Development'

# initialize argument parser
parser = argparse.ArgumentParser(description="Minus E the Art Bot - Client")
parser.add_argument('-p', '--preview',  action='store_false',   help="Toggle preview")
parser.add_argument('-b', '--botless',  action='store_true',    help="Toggle botless")
parser.add_argument('-d', '--debug',    action='store_false',   help="Toggle debug")
parser.add_argument('-o', '--out',      action='store_false',   help="Toggle output")
parser.add_argument('-i', "--image", help="path to the reference image file")

args = parser.parse_args()
BOTLESS = args.botless
PREVIEW = args.preview
DEBUG   = args.debug
OUT     = args.out
IMAGE   = args.image
 
# define the lower and upper boundaries of blue and red color of 
# the balls/markers in the HSV color space
# so far, this requires manual calibration depending on the light condition
blower = (92, 100, 0)
bupper = (112, 255, 255)
rlower = (160, 100, 100)
rupper = (179, 255, 200)

# initializing coordinates of red and blue markers
rx, ry, bx, by = 0, 0, 1, 1

# video width and height
width = 800
height = 450

# shift from the video coordinate system to canvas coordinate system
# a.k.a. the coordinate of top-left corner of canvas
sx = 265
sy = 100

# the size of the canvas
canvasw = 240
canvash = 240

# test: previous alpha value
prevAlpha = 0

# maximum error threshold in pixels
threshold = 10

# route specifies a series of coordinates that the robot will move to
center = [(width/2, height/2)]

# a few routes for testing
route1 = [(0,0),(0,50),(0,100),(50,100),(100,100),(150,100),(200,100),(250,100),(300,100),(300,50),(300,100),(250,100),(200,100),(150,100),(100,100),(50,100)]
route2 = [(0,0),(0,150),(300,150),(300,0)]
route3 = [(0,0),(0,50)]
route4 = [(0,0),(0,50)]

topLeft = (0,0)
topRight = (250,0)
bottomLeft = (0,250)
bottomRight = (250,250)
route = [topLeft]

# currP stores the index of current coordinate in route
currP = [0]

try:
    # start opencv video capture with video0
    camera = cv2.VideoCapture(0)
except 

# read reference image
img = cv2.imread(IMAGE, cv2.IMREAD_GRAYSCALE)
img = cv2.resize(img,(20, 20), interpolation = cv2.INTER_CUBIC)
#cv2.imwrite( "converted.png", img); 
route = []
values = []

for r in range(20):
    for c in range(20):
        if (r%2==0):
            route.append((6+c*canvash/20,6+r*canvasw/20))
            values.append(int((255-img[r,c])/30))
        else:
            route.append((6+(19-c)*canvash/20,6+r*canvasw/20))
            values.append(int((255-img[r,19-c])/30))
print route
print values

# getting the width and height of the video capture
#width=int(camera.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH))
#height=int(camera.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))

# initialize video output info
# codec for video output, works fine on macOS
fourcc = cv2.cv.CV_FOURCC('m','p','4','v')
if OUT:
    out = cv2.VideoWriter()
    out.open('output.mp4', fourcc, 20, (width,height))

if not BOTLESS:
    # initialize tcp connection
    serverName = '10.209.11.115'
    serverPort = 12000
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))

# go to point (dstx, dsty) on the video stream
def goTo(rx, ry, bx, by, dstx, dsty, curr):
    global prevAlpha

    #          |
    #     q2   |   q3
    #          |
    # ---------+-----------> video-x
    #          |
    #     q1   |   q0
    #          |
    #          v
    #        video-y

    #                       motor0 
    #                         |
    #                         |
    #                    rq2  |  rq3
    #                         |
    # motor3 redMarker -------+---------> blueMarker motor1 robot-x
    #                         |
    #                    rq1  |  rq0
    #                         |
    #                         v
    #                      motor2
    #                      robot-y

    # coordinates of the robot center in video coordinate system
    x = (rx+bx)/2
    y = (ry+by)/2

    # red-to-blue vector (x axis of robot coordinate system) in video coordinate system
    dx = bx-rx
    dy = by-ry
    cv2.line(frame, (int(x),int(y)), (int(dstx),int(dsty)), (255, 255, 255))

    #cv2.circle(frame, (int(x), int(y)), int(math.sqrt((rx-bx)**2+(ry-by)**2)+rradius+bradius), (255, 255, 255), -1)

    # get the slope of the Red-to-Blue vector relative of x axis of video coordinate system
    if dx != 0:
        slope = dy/dx
    else:
        slope = 100000
    
    # alpha is the rotation of  (red-to-blue vector / x axis in) robot coordinate system
    # relative to (x axis of) the video coordinate system, clockwise denotes positive
    # 0 <= alpha <= 2*pi
    alpha = math.atan(slope)
    # adjusting alpha based on which quadrant the red-to-blue vector lies
    if dx < 0:
            # when the vector is at q1, adding the angle of q0, which is pi/2
            alpha += math.pi
    elif dx == 0:   # dx == 0
        if dy > 0:
            # when the vector is on video-y, between q1 and q0
            # alpha should be precisely pi/2
            alpha = math.pi/2
        else: # dy < 0, note dy != 0 since dx == 0 and |vector| !=  0
            # when the vector is on video-y, between q2 and q3
            # alpha should be precisely 3 * pi/2
            alpha = 3*math.pi/2

    # when distance between (x,y) and (dstx, dsty) < 200 pixels
    # aka when less than 200 pixels away from destination
    # slow down the speed as the robot approaches the destination
    if math.hypot(x - dstx, y - dsty) < 200:
        speedLimit = 15 + 30 * math.hypot(x - dstx, y - dsty) / 200
    # when more than 200 pixels away from destination
    # move at "full speed"
    else:
        speedLimit = 50

    # setting a absolute speedLimit
    #speedLimit = 20

    # when less than 20 pixels away form destination (in one of those cell of the final drawing)
    #if math.hypot(x - dstx, y - dsty) < threshold:
        # pick random speed and GO
    #    v02 = randint(-5,5)
    #    v13 = randint(-5,5)
    #    speedLimit = 15
    # when out of the cell, go towards the center of the destination
    #else:
        # this vector is denoted in robot coordinate system
        # by converting from (aka rotating) the video coordinate system
        # Equation (copied below) can be found on Wikipedia, Rotation of Axes: https://en.wikipedia.org/wiki/Rotation_of_axes
        # x' = x\cos(\theta) + y\sin(\theta)
        # y' = -x\sin(\theta) + y\cos(\theta)
        # where (x', y') is the new coordinate and (x, y) is the old coordinate
        # Here, since the red-to-blue vector (x axis of robot coordinate system)
        # is parallel to the actual motor0 and motor2 (rather than the motor0-motor2 vector)
        # therefore the new x' value is assigned to v02 and y' is assigned to v13
    #    v02 = int((dstx-x)*math.cos(alpha)+(dsty-y)*math.sin(alpha))
    #    v13 = int(-(dstx-x)*math.sin(alpha)+(dsty-y)*math.cos(alpha))

    v02 = int((dstx-x)*math.cos(alpha)+(dsty-y)*math.sin(alpha))
    v13 = int(-(dstx-x)*math.sin(alpha)+(dsty-y)*math.cos(alpha))

    # This part is to handle the route
    # when less than 30 pixels away from destination
    if math.hypot(x - dstx, y - dsty) < threshold:
        if not BOTLESS:
            # pause 0.5 seconds for the robot to stop
            clientSocket.send(str([0,0,0,0,0]))
            stringFromServer = clientSocket.recv(1024)
            #time.sleep(0.1)

        if values[curr[0]] == 0:
            # switch destination to the next point in route list
            if curr[0]+1 < len(route):
                curr[0] += 1
        #        print "+"
            # goes back to the first point if the route list is finished
            else:
                curr[0] = 0
        else:
            values[curr[0]] -= 1
            print values[curr[0]]
            v02 = randint(-5,5)
            v13 = randint(-5,5)
            speedLimit = 20

    if DEBUG: print (v02, v13), int(speedLimit), (int(dstx-x), int(dsty-y)),(int(dx), int(dy)), int(math.hypot(x - dstx, y - dsty)), 2*alpha/math.pi
    # considering a simple case where the (x,y) to (dstx, dsty) vector is at rq0, then
    # the motor0 should rotate counter-clockwise (-)
    # the motor1 should rotate counter-clockwise (-)
    # the motor2 should rotate clockwise (+)
    # the motor3 should rotate clockwise (+)
    # note here clockwise/counter-clockwise is defined as the direction when you face the motor
    velocities = [-int(v02), -int(v13), int(v02), int(v13)]
    #for i in range(len(velocities)):
        #if math.hypot(x - dstx, y - dsty) < 200:
        #    velocities[i] -= int(5*(alpha - prevAlpha)*math.hypot(x - dstx, y - dsty))
        #else:
    #        velocities[i] -= int(5*(alpha - prevAlpha))
    #prevAlpha = alpha

    if not BOTLESS:
        # finally, append speedLimit to the end of the velocities list
        # convert the list to string and then send to the robot
        # the string format would be "[v0, v1, v2, v3, sl]"
        clientSocket.send(str(velocities+[int(speedLimit)]))

        # get feedback message from the server
        stringFromServer = clientSocket.recv(1024)
        if DEBUG:
            print "Server: "+stringFromServer
            print math.hypot(x - dstx, y - dsty),currP

    
while (camera.isOpened()):

    # read frame from the camera
    _, frame = camera.read()
    cv2.imwrite( "frame.jpg", frame); 

    # resize the frame, blur it, and convert it to the HSV
    # color space
    frame = imutils.resize(frame, width=width)
    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # construct a mask for the color "red" and "blue", then
    # perform a series of dilations and erosions to remove any
    # small blobs left in the mask
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

    # only proceed if at least one contour was for both red and blue
    if len(rcnts) > 0 and len(bcnts) > 0:
        # find the largest contour in the mask, then use
        # it to compute the minimum enclosing circle and
        # centroid
        rc = max(rcnts, key=cv2.contourArea)
        ((rx, ry), rradius) = cv2.minEnclosingCircle(rc)
        if DEBUG:
            rM = cv2.moments(rc)
            rcenter = (int(rM["m10"] / rM["m00"]), int(rM["m01"] / rM["m00"]))

            # only proceed if the radius meets a minimum size
            if rradius > 0 and rradius < 50:
                #print rradius, rx, ry
                # draw the circle and centroid on the frame,
                cv2.circle(frame, (int(rx), int(ry)), int(rradius),
                        (0, 255, 255), 2)
                cv2.circle(frame, rcenter, int(rradius), (0, 0, 255), -1)
                cv2.putText(frame, '3', rcenter, 0, 0.2, (255,255,255))
        bc = max(bcnts, key=cv2.contourArea)
        ((bx, by), bradius) = cv2.minEnclosingCircle(bc)
        if DEBUG:
            bM = cv2.moments(bc)
            bcenter = (int(bM["m10"] / bM["m00"]), int(bM["m01"] / bM["m00"]))

            # only proceed if the radius meets a minimum size
            if bradius > 0 and bradius < 50:
                #print bradius, bx, by
                # draw the circle and centroid on the frame,
                cv2.circle(frame, (int(bx), int(by)), int(bradius),
                        (0, 255, 255), 2)
                cv2.circle(frame, bcenter, int(bradius), (255, 0, 0), -1)
                cv2.putText(frame, '1', bcenter, 0, 0.2, (255,255,255))

    # go to the dstx and dstb
    #goTo(rx, ry, bx, by, route[currP[0]][0], route[currP[0]][1], currP)
    goTo(rx, ry, bx, by, route[currP[0]][0]+sx, route[currP[0]][1]+sy, currP)

    # show the frame to our screen
    if PREVIEW:
        #cv2.imshow("Red Mask", rmask)
        #cv2.imshow("Blue Mask", bmask)
        cv2.imshow("Frame", frame)
        #cv2.imwrite( "frame.jpg", frame); 
        #cv2.imwrite( "rmask.jpg", rmask); 
        #cv2.imwrite( "bmask.jpg", bmask); 
    # add the frame to the video file
    if OUT: out.write(frame) 

    # handle key press in opencv window
    key = cv2.waitKey(1) & 0xFF
    # if the 'q' key is pressed, stop the loop
    if key == ord("q"):
        break

# closing stuff before exiting
camera.release()
if not BOTLESS: clientSocket.close()
if OUT: out.release()
cv2.destroyAllWindows()
