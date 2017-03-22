#!/usr/bin/env python
from socket import *
import sys     # exit
import time    # sleep
import subprocess # for calling shell script
import grovepi # grovepi
import grove_i2c_motor_driver
import grove_oled

__author__ = "Jack B. Du (Jiadong Du)"
__email__ = "jackbdu@nyu.edu"
__copyright__ = "Copyright 2017, Jack B. Du (Jiadong Du)"
__license__ = "Apache-2.0"
__status__ = "Development"

OLED = False
CONSOLE = False

BUZZER_PIN = 15
# pin numbers for ultrasonic rangers # note D14 corresponds to A0
MOTORS02_ADDR = 0x0f
MOTORS13_ADDR = 0x0a

loopCount = 0

if OLED:
    # initialize oled
    grove_oled.oled_init()
    grove_oled.oled_clearDisplay()
    grove_oled.oled_setNormalDisplay()
    grove_oled.oled_setVerticalMode()
# initialize buzzer
grovepi.pinMode(BUZZER_PIN,"OUTPUT")

# socket init
serverPort = 12000
serverSocket = socket(AF_INET,SOCK_STREAM)
serverSocket.bind(('',serverPort))
serverSocket.listen(1)
if CONSOLE:
    print 'The server is running'

velocities = [1, 1, 1, 1]
speedLimit = 100

# initalize motors and return two motor pairs, 02 and 13
def initMotors():
    if CONSOLE:
        print("initializeing motors")
    # motor driver addresses accordingly
    motors02 = grove_i2c_motor_driver.motor_driver(address=MOTORS02_ADDR)
    motors13 = grove_i2c_motor_driver.motor_driver(address=MOTORS13_ADDR)
    return motors02, motors13

# set the velocities of the motors with the speedLimit as the fastest speed allowed
def setVelocities((motors02, motors13), velocities, speedLimit):
    if CONSOLE:
        print("setting velocities")
    # get directions from the velocities
    directions02 = (1 if velocities[0] >= 0 else 2) * 4 + (1 if velocities[2] >= 0 else 2)
    directions13 = (1 if velocities[1] >= 0 else 2) * 4 + (1 if velocities[3] >= 0 else 2)
    limitSpeeds(velocities, speedLimit)
    # set speeds
    motors02.MotorSpeedSetAB(abs(velocities[2]), abs(velocities[0]))    #defines the speed of motor 0 and motor 2
    motors13.MotorSpeedSetAB(abs(velocities[3]), abs(velocities[1]))    #defines the speed of motor 1 and motor 3
    # set directions
    motors02.MotorDirectionSet(directions02)
    motors13.MotorDirectionSet(directions13)

# change the fastest speed to speedLimit and scale other speeds proportionally
def limitSpeeds(velocities, speedLimit):
    if CONSOLE:
        print("converting speed")
    speedLimit += 0.0
    maxSpeed = max(abs(max(velocities)), abs(min(velocities)))
    if maxSpeed > 0:
        for i in range(4):
            velocities[i] *= speedLimit/maxSpeed

# stop motors
def stop(motors):
    if CONSOLE:
        print("stopping the motors")
    #STOP
    setVelocities(motors, [0,0,0,0], 0);
    time.sleep(1)

def main():
    try:
        try:
            motors = initMotors()
                
        except IOError:
            print("Unable to find the motor driver, check the addrees and press reset on the motor driver and try again")
            
        while True:
            try:
                time.sleep(0.01)

                while True:
                    connectionSocket, addr = serverSocket.accept()

                    x = 0
                    while x != chr(27):
                        x = connectionSocket.recv(1024)
                        print "Client:", x
                        if (x=='w' or x=='k'):    # forward
                            velocities = [10,10,10,10]
                            speedLimit = 10
                        elif (x=='s' or x=='j'):  # backward
                            velocities = [10,10,10,10]
                            speedLimit = 10
                        elif (x=='a' or x=='h'):  # turn left
                            velocities = [10,10,10,10]
                            speedLimit = 10
                        elif (x=='d' or x=='l'):  # turn right
                            velocities = [10,10,10,10]
                            speedLimit = 10
                        elif (x==' '):  # stop
                            speedLimit = 0

                        if CONSOLE:
                            print("-------------------- "+str(loopCount)+" --------------------")
                            print("R: " + str(rotation))
                            print("D: " + str(distances))
                            print("V: " + str([int(i) for i in velocities]))
                            loopCount += 1

                        if OLED:
                            #display, note this may slow the robot reaction down
                            grove_oled.oled_setTextXY(11,0)
                            grove_oled.oled_putString("ROT:"+str(int(rotation)))
                            for i in range (len(distances)):
                                grove_oled.oled_setTextXY(i,0)
                                grove_oled.oled_putString(str(i)+":"+str(distances[i]).zfill(3))
                            for i in range(len(velocities)):
                                grove_oled.oled_setTextXY(i,6)
                                grove_oled.oled_putString(str(i)+":"+str(int(velocities[i])).zfill(4))
                        setVelocities(motors, velocities, speedLimit)
                    stop(motors)
                    connectionSocket.close()

            except TypeError:
                print ("TypeError")
                grovepi.digitalWrite(BUZZER_PIN,1)
                subprocess.call(['./avrdude_test.sh'])
            except IOError:
                print ("IOError")
    except KeyboardInterrupt: # stop motors before exit
        # stop buzzer
        connectionSocket.close()
        grovepi.digitalWrite(BUZZER_PIN,0)
        stop(motors)
        sys.exit()

if __name__ == "__main__":
    main()
