#!/usr/bin/env python
# import the necessary packages
import os       # path
import sys      # exit
import time     # sleep
import math     # math.pi, math.sin, math.cos
import argparse # argparse
import datetime # datetime
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
parser = argparse.ArgumentParser(description="Minus E - Client")
parser.add_argument('-m', '--monitor',  action='store_true',   help="Toggle monitor")
parser.add_argument('-b', '--botless',  action='store_true',   help="Toggle botless")
parser.add_argument('-d', '--debug',    action='store_true',   help="Toggle debug")
parser.add_argument('-o', '--out',      action='store_true',   help="Toggle output")
parser.add_argument('-c', '--crop',     action='store_true',   help="Toggle crop")
parser.add_argument('-r', '--resolution',   type=int, default=20,   help="Specify the height of the drawing")
parser.add_argument('-can', '--canvas',     type=int, default=600,  help="Specify the height of the canvas")
parser.add_argument('-mar', '--margin',     type=int, default=20,   help="Specify the margin of the drawing")
parser.add_argument('-id', '--index',       type=int, default=0,    help="specify the initial index")
parser.add_argument('-dp', '--depth',       type=int, default=64,   choices=[0,2,4,8,16,32,64,128,256], help="specify the color depth")
parser.add_argument('-i', '--image', help="path to the reference image file")
parser.add_argument('-p', '--perspective',  nargs='+', help="specify the corners of canvas")
args = parser.parse_args()

BOTLESS = args.botless
MONITOR = args.monitor
DEBUG   = args.debug
OUT     = args.out
CROP    = args.crop
RES     = (args.resolution, args.resolution) # for now, assume it's square
CANVAS  = args.canvas
IMAGE   = args.image
MARGIN  = args.margin
DEPTH   = args.depth
PERS    = args.perspective
# currIndex stores the index of current coordinate in route
currIndex = args.index
OUTPATH = datetime.datetime.now().strftime('%s_%Y%m%d_')  + (IMAGE+'_output/' if IMAGE else 'generated_output/')
frameCount = 0
isPaused = True
 
# colors in BGR for convenience
BLACK   = (0, 0, 0)
WHITE   = (255, 255, 255)
BLUE    = (255, 0, 0)
GREEN   = (0, 255, 0)
RED     = (0, 0, 255)

# define the lower and upper boundaries of blue and red color of 
# the balls/markers in the HSV color space
# so far, this requires manual calibration depending on the light condition
# (0-179, 0-255, 0-255)
blower = (92, 100, 0)
bupper = (112, 255, 255)
rlower = (160, 100, 100)
rupper = (179, 255, 200)

# video width and height
videoSize = (1600, 900)

# shift from the video coordinate system to canvas coordinate system
# a.k.a. the coordinate of top-left corner of canvas
cropShift = (400, 80)
if CROP:
    canvasShift = (MARGIN, MARGIN)
else:
    canvasShift = (cropShift[0]+MARGIN, cropShift[1]+MARGIN)

# initializing coordinates of red and blue markers
# [redX, redY, blueX, blueY]
markers        = [-1, -1, -1, -1]
virtualMarkers = [canvasShift[0]-25, canvasShift[1], canvasShift[0]+25, canvasShift[1]]

# maximum speed
MAXSPEED = 50

if not os.path.exists(OUTPATH):
    os.makedirs(OUTPATH)

if IMAGE:
    # read reference image, resize and save it
    img = cv2.imread(IMAGE, cv2.IMREAD_GRAYSCALE)
    # initializing mouse click callback
    h, w = img.shape
    RES = (args.resolution*w/h, args.resolution) # for now, assume it's square
    img = cv2.resize(img, RES, interpolation = cv2.INTER_AREA)
    cv2.imwrite(OUTPATH+IMAGE+'_converted.png', img); 

log = open(OUTPATH+"log.txt", "w")
log.write(str(args))
log.close()

# the exact size of the canvas/paper
canvasSize = (CANVAS*RES[0]/RES[1], CANVAS)
canvasSize = (canvasSize[0]-2*MARGIN, canvasSize[1]-2*MARGIN)

# the monitor window size
windowSize = (canvasSize[0]+MARGIN*4, canvasSize[1]+MARGIN*4)

# maximum error threshold in pixels
threshold = canvasSize[0]/RES[0]/2

route   = [] # a route of coordinates
values  = [] # values/darkness of pixels
trace   = [] # trace of virtual bot, for displaying virtual drawing

for r in range(RES[1]): # for each row
    for c in range(RES[0]): # for each column
        # even number of rows
        if (r%2==0):
            route.append((MARGIN+c*canvasSize[0]/(RES[0]-1),
                          MARGIN+r*canvasSize[1]/(RES[1]-1)))
            # add value of the pixel if image is provided
            if IMAGE:
                values.append(int((255-img[r,c])*DEPTH/256))
            # add random value if no image
            else:
                values.append(randint(0,255)*DEPTH/256)
        # odd number of rows
        else:
            route.append((MARGIN+(RES[0]-1-c)*canvasSize[0]/(RES[0]-1),
                          MARGIN+r*canvasSize[1]/(RES[1]-1)))
            # add value of the pixel if image is provided
            if IMAGE:
                values.append(int((255-img[r,RES[0]-1-c])*DEPTH/256))
            # add random value if no image
            else:
                values.append(randint(0,255)*DEPTH/256)

if not IMAGE:
    IMAGE = "generated"

if currIndex >= len(route):
    print "Initial Index Error: Please check the index you specified"
    sys.exit(1)

if DEBUG:
    print "  Route:", route
    print " Values:", values

# getting the width and height of the video capture
#width=int(camera.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH))
#height=int(camera.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))

if not BOTLESS:
    # initialize tcp connection
    serverName = 'minusetheartbot.local'
    serverPort = 12000
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))

# points before transform
perspectiveCorners = []
if (PERS):
    for i in range(4):
        perspectiveCorners.append([PERS[i*2], PERS[i*2+1]])

def mouseCallback(event,x,y,flags,param):
    # add perspective point
    if event == cv2.EVENT_LBUTTONDOWN:
        if (len(perspectiveCorners) < 4):
            perspectiveCorners.append([x, y]);
        if DEBUG:
            print "Perspective Corners: "+str(perspectiveCorners)
            print "HSV Color: "+str(cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)[y,x])

# reference image window
imgShow = cv2.imread(IMAGE, cv2.IMREAD_COLOR)
imgShow = cv2.resize(imgShow, (windowSize[0]/2,windowSize[1]/2), interpolation = cv2.INTER_AREA)
cv2.imshow("Reference", imgShow)
cv2.namedWindow("Reference")

# initializing mouse click callback
cv2.namedWindow('Monitor')
cv2.setMouseCallback('Monitor', mouseCallback)

# arrange windows
cv2.moveWindow("Monitor", 0, 0);
cv2.moveWindow("Reference", windowSize[0], 0);

# go to point (dstx, dsty) on the video stream
def goTo((rx, ry, bx, by), (dstx, dsty), curr):
    global virtualMarkers
    global frameCount

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

    # if color is detected
    if (rx != -1):
        # coordinates of the robot center in video coordinate system
        x, y = (rx+bx)/2, (ry+by)/2

        # red-to-blue vector (x axis of robot coordinate system) in video coordinate system
        dx, dy = bx-rx, by-ry

        # line from robot to dest
        cv2.line(frame, (int(x),int(y)), (int(dstx),int(dsty)), WHITE)

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
            speedLimit = MAXSPEED/4 + MAXSPEED/2 * math.hypot(x - dstx, y - dsty) / 200
        # when more than 200 pixels away from destination
        # move at "full speed"
        else:
            speedLimit = MAXSPEED

        # this vector is denoted in robot coordinate system
        # by converting from (aka rotating) the video coordinate system
        # Equation (copied below) can be found on Wikipedia, Rotation of Axes: https://en.wikipedia.org/wiki/Rotation_of_axes
        # x' = x\cos(\theta) + y\sin(\theta)
        # y' = -x\sin(\theta) + y\cos(\theta)
        # where (x', y') is the new coordinate and (x, y) is the old coordinate
        # Here, since the red-to-blue vector (x axis of robot coordinate system)
        # is parallel to the actual motor0 and motor2 (rather than the motor0-motor2 vector)
        # therefore the new x' value is assigned to v02 and y' is assigned to v13
        v02 = int((dstx-x)*math.cos(alpha)+(dsty-y)*math.sin(alpha))
        v13 = int(-(dstx-x)*math.sin(alpha)+(dsty-y)*math.cos(alpha))

        # This part is to handle the route
        # when less than threshold pixels away from destination
        if math.hypot(x - dstx, y - dsty) < threshold:
            if not BOTLESS:
                # pause 0.5 seconds for the robot to stop
                clientSocket.send(str([0,0,0,0,0]))
                stringFromServer = clientSocket.recv(1024)
                #time.sleep(0.1)

            if values[curr] % 2 == 0:
                cv2.imwrite(OUTPATH+IMAGE+"_"+str(frameCount).zfill(8)+".jpg", fullFrame)
                frameCount += 1


            # when current current index is done
            if values[curr] <= 0:
                # add the frame to the video file
                if OUT:
                    if not BOTLESS and IMAGE:
                        cv2.imwrite(OUTPATH+IMAGE+"_"+str(curr).zfill(len(str(len(route)))+1)+".jpg", fullFrame);
                # switch destination to the next point in route list
                if curr+1 < len(route):
                    curr += 1
            #        print "+"
                # goes back to the first point if the route list is finished
                else:
                    #curr = 0
                    if BOTLESS: print trace
                    if IMAGE: cv2.imwrite(OUTPATH+IMAGE+"_final.jpg", frame); 
                    
            # when current index isn't done
            else:
                values[curr] -= 1
                # generate random velocities
                v02 = randint(-5,5)
                v13 = randint(-5,5)
                speedLimit = 20
                if BOTLESS:
                    dstx += v02*3
                    dsty += v13*3

        if DEBUG:
            # debug info displayed in monitor
            cv2.putText(frame, "V02: "+str(v02), (70,15), 0, 0.35, BLACK)
            cv2.putText(frame, "V13: "+str(v13), (140,15), 0, 0.35, BLACK)
            cv2.putText(frame, "LMT: "+str(int(speedLimit)), (210,15), 0, 0.35, BLACK)
            cv2.putText(frame, "DIST: "+str(int(math.hypot(x - dstx, y - dsty))), (280,15), 0, 0.35, BLACK)
            cv2.putText(frame, "IDX: "+str(curr), (350,15), 0, 0.35, BLACK)
            cv2.putText(frame, "VAL: "+str(values[curr]), (420,15), 0, 0.35, BLACK)
            print "    Velocities:", (v02, v13), int(speedLimit)
            print "  Dist to Dest:", int(math.hypot(x - dstx, y - dsty))
            print " Current Point:", curr
            print " Current Value:", values[curr]
        # considering a simple case where the (x,y) to (dstx, dsty) vector is at rq0, then
        # the motor0 should rotate counter-clockwise (-)
        # the motor1 should rotate counter-clockwise (-)
        # the motor2 should rotate clockwise (+)
        # the motor3 should rotate clockwise (+)
        # note here clockwise/counter-clockwise is defined as the direction when you face the motor
        velocities = [-int(v02), -int(v13), int(v02), int(v13)]
    # if either color is not detected
    else:
        velocities = [0,0,0,0]
        speedLimit = 0
        x = -1
        y = -1

    if BOTLESS:
        virtualMarkers[0] += int((dstx-x)*speedLimit/50)
        virtualMarkers[1] += int((dsty-y)*speedLimit/50)
        virtualMarkers[2] += int((dstx-x)*speedLimit/50)
        virtualMarkers[3] += int((dsty-y)*speedLimit/50)
    else:
        # finally, append speedLimit to the end of the velocities list
        # convert the list to string and then send to the robot
        # the string format would be "[v0, v1, v2, v3, sl]"
        clientSocket.send(str(velocities+[int(speedLimit)]))

        # get feedback message from the server
        stringFromServer = clientSocket.recv(1024)
        if DEBUG:
            if stringFromServer == "OK":
                cv2.putText(frame, "SVR: "+stringFromServer, (10, 15), 0, 0.35, GREEN)
            else:
                cv2.putText(frame, "SVR: "+stringFromServer, (10, 15), 0, 0.35, RED)
            print "Server: "+stringFromServer

    # output frame with info
    if IMAGE and math.hypot(x - dstx, y - dsty) < threshold and values[curr] <= 0:
        cv2.imwrite(OUTPATH+IMAGE+"_info_"+str(curr).zfill(len(str(len(route)))+1)+".jpg", frame);

    return curr

    
# start opencv video capture with video0
camera = cv2.VideoCapture(0)
#camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)

while (camera.isOpened()):

    # read frame from the camera
    _, fullFrame = camera.read()

    # resize the frame
    frame = imutils.resize(fullFrame, width=videoSize[0])

   
    if CROP: frame = frame[cropShift[1]:cropShift[1]+canvasSize[1]+MARGIN*4, cropShift[0]:cropShift[0]+canvasSize[0]+MARGIN*4]

    # transform
    if (len(perspectiveCorners) > 3):
        rows,cols,ch = frame.shape
        pts1 = np.float32(perspectiveCorners[:4])
        pts2 = np.float32([[0,0],[rows/RES[1]*RES[0],0],[rows/RES[1]*RES[0],rows],[0,rows]])
        M = cv2.getPerspectiveTransform(pts1,pts2)
        frame = cv2.warpPerspective(frame,M,(cols,rows))
 

    # virtual bot simulation
    if BOTLESS:

        markers[0] = virtualMarkers[0]
        markers[1] = virtualMarkers[1]
        markers[2] = virtualMarkers[2]
        markers[3] = virtualMarkers[3]
        rradius = 12
        bradius = 12
        rcenter = (markers[0], markers[1])
        bcenter = (markers[2], markers[3])
        x = (markers[2]+markers[0])/2
        y = (markers[3]+markers[1])/2

        # add the current virtual robot coordinate to trace
        trace.append((x,y))

        # draw the trace on screen
        if len(trace) > 1:
            for i in range(len(trace)-1):
                # draw line from every two points
                cv2.line(frame, trace[i], trace[i+1], BLACK, 1)

        # draw the robot
        cv2.circle(frame, (int(x), int(y)), int((math.sqrt((markers[0]-markers[2])**2+(markers[1]-markers[3])**2)+rradius+bradius)/2+5), BLACK, -1)
        cv2.circle(frame, (int(x), int(y)), int((math.sqrt((markers[0]-markers[2])**2+(markers[1]-markers[3])**2)+rradius+bradius)/2+5), WHITE, 1)

        # draw the red marker
        cv2.circle(frame, rcenter, int(rradius), RED, -1)
        cv2.circle(frame, (int(markers[0]), int(markers[1])), int(rradius), WHITE, 1)
        cv2.putText(frame, '3', rcenter, 0, 0.4, WHITE)

        # draw the blue marker
        cv2.circle(frame, bcenter, int(bradius), BLUE, -1)
        cv2.circle(frame, (int(markers[2]), int(markers[3])), int(bradius), WHITE, 1)
        cv2.putText(frame, '1', bcenter, 0, 0.4, WHITE)

    else:
        # blur the frame, and convert it to the HSV color space
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
            ((markers[0], markers[1]), rradius) = cv2.minEnclosingCircle(rc)
            bc = max(bcnts, key=cv2.contourArea)
            ((markers[2], markers[3]), bradius) = cv2.minEnclosingCircle(bc)
            # faulty markers if either radius is too large or distance between markers is too large
            if rradius > 50 or bradius > 50 or math.hypot(markers[0]-markers[2], markers[1]-markers[3]) > 100:
                markers = [-1,-1,-1,-1]

            if DEBUG:
                rM = cv2.moments(rc)
                rcenter = (int(rM["m10"] / rM["m00"]), int(rM["m01"] / rM["m00"]))

                # only proceed if the radius meets a minimum size
                if rradius > 0 and rradius < 50:
                    #print rradius, rx, ry
                    # draw the circle and centroid on the frame,
                    cv2.circle(frame, rcenter, int(rradius), RED, -1)
                    cv2.circle(frame, (int(markers[0]), int(markers[1])), int(rradius), WHITE, 1)
                    #cv2.putText(frame, '3', rcenter, 0, 0.4, WHITE)

                bM = cv2.moments(bc)
                bcenter = (int(bM["m10"] / bM["m00"]), int(bM["m01"] / bM["m00"]))

                # only proceed if the radius meets a minimum size
                if bradius > 0 and bradius < 50:
                    #print bradius, bx, by
                    # draw the circle and centroid on the frame,
                    cv2.circle(frame, bcenter, int(bradius), BLUE, -1)
                    cv2.circle(frame, (int(markers[2]), int(markers[3])), int(bradius), WHITE, 1)
                    #cv2.putText(frame, '1', bcenter, 0, 0.4, WHITE)
        # if either color is not detected
        else:
            markers = [-1,-1,-1,-1]

    # the grid is drawn at the end so as not to affect the tracking
    if DEBUG:
        for c in range(RES[0]):
            cv2.line(frame, (route[c][0]+canvasShift[0], route[0][1]+canvasShift[1]), (route[c][0]+canvasShift[0], route[-1][1]+canvasShift[1]), WHITE, 1)
        for r in range(RES[1]):
            cv2.line(frame, (route[0][0]+canvasShift[0], route[r*RES[0]][1]+canvasShift[1]), (route[RES[0]-1][0]+canvasShift[0], route[r*RES[0]][1]+canvasShift[1]), WHITE, 1)

    if isPaused:
        markers = [-1,-1,-1,-1]

    # go to the dstx and dstb
    #goTo(rx, ry, bx, by, route[currIndex[0]][0], route[currIndex[0]][1], currIndex)
    dst = (route[currIndex][0]+canvasShift[0], route[currIndex][1]+canvasShift[1])
    currIndex = goTo(markers, dst, currIndex)

    # show the frame to our screen
    if MONITOR:
        #cv2.imshow("Red Mask", rmask)
        #cv2.imshow("Blue Mask", bmask)
        cv2.imshow("Monitor", frame)
        #cv2.imwrite(OUTPATH+"frame.jpg", frame); 
        #cv2.imwrite(OUTPATH+"rmask.jpg", rmask); 
        #cv2.imwrite(OUTPATH+"bmask.jpg", bmask); 

    # handle key press in opencv window
    key = cv2.waitKey(1) & 0xFF
    # if the 'q' key is pressed, stop the loop
    if key == ord("q"):
        break
    elif key == ord(" "):
        isPaused = not isPaused
        print isPaused

# closing stuff before exiting
camera.release()
if not BOTLESS: clientSocket.close()
cv2.destroyAllWindows()
