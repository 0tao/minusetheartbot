#!/usr/bin/env python
from socket import *
import sys     # exit
import time    # sleep
import subprocess # for calling shell script
import argparse # argparse
try:
    from lib import grovepi # grovepi
    from lib import grove_i2c_motor_driver
    from lib import grove_oled
except ImportError as error:
    print "ImportError:", error.args[0]
    sys.exit(1)

__author__ = "Jack B. Du (Jiadong Du)"
__email__ = "jackbdu@nyu.edu"
__copyright__ = "Copyright 2017, Jack B. Du (Jiadong Du)"
__license__ = "Apache-2.0"
__status__ = "Development"

parser = argparse.ArgumentParser(description="Minus E the Art Bot")
parser.add_argument('-p', '--port', type=int, default=12000, help="specify the port number")
parser.add_argument('-o', '--oled', action='store_true', help="Toggle OLED display")
parser.add_argument('-d', '--debug', action='store_true', help="Toggle debugging info")

args = parser.parse_args()

OLED = args.oled
CONSOLE = args.debug

BUZZER_PIN = 15
# pin numbers for ultrasonic rangers # note D14 corresponds to A0
MOTORS02_ADDR = 0x0f
MOTORS13_ADDR = 0x0a

# initalize motors and return two motor pairs, 02 and 13
def initMotors():
    if CONSOLE: print("Initializeing motors ...")
    # motor driver addresses accordingly
    motors02 = grove_i2c_motor_driver.motor_driver(address=MOTORS02_ADDR)
    motors13 = grove_i2c_motor_driver.motor_driver(address=MOTORS13_ADDR)
    return motors02, motors13

# set the velocities of the motors with the speedLimit as the fastest speed allowed
def setVelocities((motors02, motors13), velocities, speedLimit):
    if CONSOLE: print("Setting velocities ...")
    # get directions from the velocities
    directions02 = (1 if velocities[0] >= 0 else 2) * 4 + (1 if velocities[2] >= 0 else 2)
    directions13 = (1 if velocities[1] >= 0 else 2) * 4 + (1 if velocities[3] >= 0 else 2)
    limitSpeeds(velocities, speedLimit)
    try:
        # set speeds
        motors02.MotorSpeedSetAB(abs(velocities[2]), abs(velocities[0]))    #defines the speed of motor 0 and motor 2
        motors13.MotorSpeedSetAB(abs(velocities[3]), abs(velocities[1]))    #defines the speed of motor 1 and motor 3
        # set directions
        motors02.MotorDirectionSet(directions02)
        motors13.MotorDirectionSet(directions13)
    except IOError:
        if CONSOLE:
            print "IOError:", "Unable to find the motor driver, check the address and press reset on the motor driver and try again"
        return 1

    return 0

# change the fastest speed to speedLimit and scale other speeds proportionally
def limitSpeeds(velocities, speedLimit):
    if CONSOLE: print("Limiting speed ...")
    speedLimit += 0.0
    maxSpeed = max(abs(max(velocities)), abs(min(velocities)))
    if maxSpeed > 0:
        for i in range(4):
            velocities[i] *= speedLimit/maxSpeed

# stop motors
def stop(motors):
    if CONSOLE: print("Stopping motors ...")
    #STOP
    setVelocities(motors, [0,0,0,0], 0);
    time.sleep(1)

def main():

    # initialize velocities and speedLimit
    # the speedLimit specifies a hard max limit for all wheels
    velocities = [0, 0, 0, 0]
    speedLimit = 0
    loopCount = 0

    if OLED:
        if CONSOLE: print 'Initializing OLED ...'
        # initialize oled
        grove_oled.oled_init()
        grove_oled.oled_clearDisplay()
        grove_oled.oled_setNormalDisplay()
        grove_oled.oled_setVerticalMode()

    # initialize buzzer
    grovepi.pinMode(BUZZER_PIN,"OUTPUT")

    if CONSOLE: print 'Initializing server ...'
    try:
        # initialize socket
        serverPort = args.port
        serverSocket = socket(AF_INET,SOCK_STREAM)
        serverSocket.bind(('',serverPort))
        serverSocket.listen(1)
    except OverflowError as error:
        print "OverflowError:", error.args[0]
        sys.exit(1)

    if CONSOLE: print 'Starting up the server'

    try:
        try:
            motors = initMotors()
                
        except IOError:
            print "IOError:", "Unable to find the motor driver, check the address and press reset on the motor driver and try again"
            
        while True:
            try:
                time.sleep(0.01)

                while True:
                    if CONSOLE: print("Waiting for connection ...")
                    # listening for connection
                    connectionSocket, addr = serverSocket.accept()

                    if CONSOLE: print("Connected to " + str(addr) + " ...")
                    connected = True
                    while connected:
                        if CONSOLE: print("Waiting for message ...")
                        stringFromClient = connectionSocket.recv(1024)
                        if CONSOLE: print "Message received: ", stringFromClient

                        try: 
                            # converting string to int list
                            # message format: [v0, v1, v2, v3, sl]
                            listFromClient = map(int, stringFromClient.lstrip('[').rstrip(']').split(', '))
                            # slice the velocities list
                            velocities = listFromClient[:4]
                            # slice the speedLimit
                            speedLimit = listFromClient[-1]

                            if OLED:
                                #display, note this may slow the robot reaction down
                                grove_oled.oled_setTextXY(11,0)
                                for i in range(len(velocities)):
                                    grove_oled.oled_setTextXY(i,6)
                                    grove_oled.oled_putString(str(i)+":"+str(int(velocities[i])).zfill(4))
                            if CONSOLE:
                                print("-------------------- "+str(loopCount)+" --------------------")
                                print("V: " + str([int(i) for i in velocities]))
                                print("L: " + str(speedLimit))
                                loopCount += 1

                        except:
                            if CONSOLE: print "Converting message Error: ", stringFromClient

                        if CONSOLE: print "Setting the velocities ..."

                        # set the velocities
                        if setVelocities(motors, velocities, speedLimit):
                            if CONSOLE: print "Sending BAD to client ..."
                            connectionSocket.send("BAD")
                        else:
                            if CONSOLE: print "Sending OK to client ..."
                            connectionSocket.send("OK")

                    if CONSOLE: print("Disconnected to " + str(addr) + "!")
                    stop(motors)
                    if CONSOLE: print("Closing the socket " + str(addr) + " ...")
                    connectionSocket.close()
                    loopCount = 0

            except TypeError:
                print ("TypeError")
                grovepi.digitalWrite(BUZZER_PIN,1)
                subprocess.call(['./lib/avrdude_test.sh'])
            except IOError as error:
                print "IOError:", error.args[1]
                if CONSOLE: print("Disconnected to " + str(addr) + "!")
            stop(motors)
            connectionSocket.close()
            loopCount = 0
    except KeyboardInterrupt: # stop motors before exit
        if CONSOLE: print("Keyboard Interrput!")
        connectionSocket.close()
        grovepi.digitalWrite(BUZZER_PIN,0)
        stop(motors)
        sys.exit()

if __name__ == "__main__":
    main()
