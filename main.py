#!/usr/bin/env python
import sys     # exit
import time    # sleep
import subprocess # for calling shell script
import grovepi # grovepi
import grove_i2c_motor_driver
import grove_oled
import itg3200 # library for grove gyroscope

__author__ = "Jack B. Du (Jiadong Du)"
__email__ = "jackbdu@nyu.edu"
__copyright__ = "Copyright 2017, Jack B. Du (Jiadong Du)"
__license__ = "Apache-2.0"
__status__ = "Development"

OLED = False
CONSOLE = True

BUZZER_PIN = 15
# pin numbers for ultrasonic rangers # note D14 corresponds to A0
ULTRASONIC_RANGERS_PINS = (8, 4, 3, 14, 2, 5, 7, 6)
GYRO_ADDR = 0x68
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

# update with your bus number and address
gyro = itg3200.SensorITG3200(1, GYRO_ADDR)
gyro.default_init()

distances = [0] * 8
# + denote clockwise, - denote counter-clockwise
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

# get the distances from each ultrasonic ranger
def getDistances(distances):
    if CONSOLE:
        print("reading ultrasonic rangers")
    for i in range(len(ULTRASONIC_RANGERS_PINS)):
        distances[i] = grovepi.ultrasonicRead(ULTRASONIC_RANGERS_PINS[i])

# get rotation from gyroscope
def getRotation():
    # storing the z-axis gyro value
    return gyro.read_data()[2]+40
# avoid getting hit
def avoidObstacles(distances, velocities):
    if CONSOLE:
        print("handling obstacles")
    reactDistance = 100
    for i in range(len(distances)):
        if distances[i] < reactDistance:
            velocities[(i/2+1)%4] -= reactDistance-distances[i]
            velocities[(i/2+3)%4] += reactDistance-distances[i]
            # if the ranger is between two motors
            if i%2 == 1:
                velocities[(i/2+2)%4] -= reactDistance-distances[i]
                velocities[(i/2+4)%4] += reactDistance-distances[i]

def explore(distances, velocities):
    if CONSOLE:
        print("exploring")
    for i in range(len(distances)):
        if distances[i] > 300:
            velocities[(i/2+1)%4] += (distances[i]-300)/10
            velocities[(i/2+3)%4] -= (distances[i]-300)/10
            # if the ranger is between two motors
            if i%2 == 1:
                velocities[(i/2+2)%4] += (distances[i]-300)/10
                velocities[(i/2+4)%4] -= (distances[i]-300)/10
            break

def correctRotation(rotation, velocities):
    if CONSOLE:
        print("correcting rotation")
    if rotation < 0: 
        for i in range(len(velocities)):
            velocities[i] += (0-rotation)/10
    elif rotation > 10:
        for i in range(len(velocities)):
            velocities[i] -= (rotation-10)/10

# stop motors
def stop(motors):
    if CONSOLE:
        print("stopping the motors")
    #STOP
    setVelocities(motors, [0,0,0,0], 0);
    time.sleep(1)

try:
    try:
        motors = initMotors()
            
    except IOError:
        print("Unable to find the motor driver, check the addrees and press reset on the motor driver and try again")
        
    while True:
        try:
            time.sleep(0.01)
            rotation = getRotation()
            correctRotation(rotation, velocities)
            # Read distance value from Ultrasonic
            getDistances(distances)
            explore(distances, velocities)
            avoidObstacles(distances, velocities)
            setVelocities(motors, velocities, speedLimit)

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
            grovepi.digitalWrite(BUZZER_PIN,0)

        except TypeError:
            print ("TypeError")
            grovepi.digitalWrite(BUZZER_PIN,1)
            subprocess.call(['./avrdude_test.sh'])
        except IOError:
            print ("IOError")
except KeyboardInterrupt: # stop motors before exit
    # stop buzzer
    grovepi.digitalWrite(BUZZER_PIN,0)
    stop(motors)
    sys.exit()
