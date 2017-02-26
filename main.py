#!/usr/bin/env python

import sys
import grovepi
import grove_i2c_motor_driver
import itg3200
import time

# pin numbers for ultrasonic rangers
us_ranger_f = 8
us_ranger_b = 2
us_ranger_l = 7
us_ranger_r = 3
# update with your bus number and address
gyro = itg3200.SensorITG3200(1, 0x68)
gyro.default_init()
# lists storing speeds
lr_s = [100, 100]
fb_s = [100, 100]
# 0 denote clockwise, 1 denote counter-clockwise
directions = [0, 0, 0, 0]
speeds = [50, 100, 100, 100]
speedLimit = 50

def setDirections((motors02, motors13), directions):
    directions02 = (directions[0]+1) * 4 + (directions[2]+1)
    directions13 = (directions[1]+1) * 4 + (directions[3]+1)
    motors02.MotorDirectionSet(directions02)
    motors13.MotorDirectionSet(directions13)

def setSpeeds((motors02, motors13), speeds, speedLimit):
    limitSpeeds(speeds, speedLimit)
    motors02.MotorSpeedSetAB(speeds[2], speeds[0])    #defines the speed of motor 0 and motor 2
    motors13.MotorSpeedSetAB(speeds[3], speeds[1])    #defines the speed of motor 1 and motor 3

def limitSpeeds(speeds, speedLimit):
    speedLimit += 0.0
    maxSpeed = max(speeds)
    if maxSpeed > 0:
        for i in range(4):
            if speeds[i] == maxSpeed:
                speeds[i] = speedLimit
            else:
                speeds[i] *= speedLimit/maxSpeed
            
# normalize the speed by setting the faster wheel to ms
# and scale the other wheel speed accordingly
def normalize_s(xx_s, ms):
    # set ms to 100 if out of boundary
    if (ms > 100 or ms < 0):
        ms = 100.0
    else:
        ms += 0.0

    if (xx_s[1] <= xx_s[0]):
        xx_s[1] *= ms/xx_s[0]
        xx_s[0] = ms
    elif (xx_s[0] <= xx_s[1]):
        xx_s[0] *= ms/xx_s[1]
        xx_s[1] = ms
    print xx_s

def forward(mlr, lr_s, gz):
    #FORWARD
    print("Forward")
    if gz < -10: #turning closewise
        lr_s[0] *= 95/100.0
        lr_s[1] *= 100/95.0
        
    elif gz > 10: #turning counter-clockwise
        lr_s[0] *= 100/95.0
        lr_s[1] *= 95/100.0
    normalize_s(lr_s, 50)
    mlr.MotorSpeedSetAB(lr_s[0], lr_s[1])    #defines the speed of motor 1 and motor 2;
    mlr.MotorDirectionSet(0b0110)    #"0b1010" defines the output polarity, "10" means the M+ is "positive" while the M- is "negtive"

def backward(mlr, lr_s, gz):
    #BACKWARD
    print("Backward")
    if gz < -10: #turning closewise
        lr_s[0] *= 100/95.0
        lr_s[1] *= 95/100.0
        
    elif gz > 10: #turning counter-clockwise
        lr_s[0] *= 95/100.0
        lr_s[1] *= 100/95.0
    normalize_s(lr_s, 50)
    mlr.MotorSpeedSetAB(lr_s[0], lr_s[1])    #defines the speed of motor 1 and motor 2;
    mlr.MotorDirectionSet(0b1001)    #0b0101    Rotating in the opposite direction

def leftward(mfb, fb_s, gz):
    #LEFTWARD
    print("Leftward")
    forward(mfb, fb_s, gz)

def rightward(mfb, fb_s, gz):
    #RIGHTWARD
    print("RIGHTWARD")
    backward(mfb, fb_s, gz)

def stop(motors):
    #STOP
    print("Stop")
    setSpeeds(motors, [0,0,0,0], 0);
    time.sleep(1)

try:
    try:
        motors02 = grove_i2c_motor_driver.motor_driver(address=0x0f)
        motors13 = grove_i2c_motor_driver.motor_driver(address=0x0a)
        motors = (motors02, motors13)
        motors02.MotorSpeedSetAB(100,100)
        motors13.MotorSpeedSetAB(100,100)
        setDirections(motors, directions)
        print(directions)
        setSpeeds(motors, speeds, speedLimit)
        print(speeds)
            
    except IOError:
        print("Unable to find the motor driver, check the addrees and press reset on the motor driver and try again")
        
    while True:
        try:
            time.sleep(0.1)
            # storing the z-axis gyro value
            gz = gyro.read_data()[2]+40
            print gz
            # Read distance value from Ultrasonic
            dist_f = grovepi.ultrasonicRead(us_ranger_f)
            dist_b = grovepi.ultrasonicRead(us_ranger_b)
            dist_l = grovepi.ultrasonicRead(us_ranger_l)
            dist_r = grovepi.ultrasonicRead(us_ranger_r)
            print(dist_f, dist_r, dist_b, dist_l)


        except TypeError:
            print ("Error")
        except IOError:
            print ("Error")
except KeyboardInterrupt: # stop motors before exit
    stop(motors)
    sys.exit()
