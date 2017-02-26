#!/usr/bin/env python

import sys
import grovepi
import grove_i2c_motor_driver
import itg3200
import time

us_ranger_f = 8
us_ranger_b = 2
us_ranger_l = 7
us_ranger_r = 3
gyro = itg3200.SensorITG3200(1, 0x68) # update with your bus number and address
gyro.default_init()
lr_s = [100, 100]
fb_s = [100, 100]

def normalize_s(xx_s):
    if (xx_s[1] <= xx_s[0]):
        xx_s[1] *= 100.0/xx_s[0]
        xx_s[0] = 100
    elif (xx_s[0] <= xx_s[1]):
        xx_s[0] *= 100.0/xx_s[1]
        xx_s[1] = 100
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
    normalize_s(lr_s)
    mlr.MotorSpeedSetAB(lr_s[0], lr_s[1])    #defines the speed of motor 1 and motor 2;
    mlr.MotorDirectionSet(0b0110)    #"0b1010" defines the output polarity, "10" means the M+ is "positive" while the M- is "negtive"

def backward(mlr, s):
    #BACKWARD
    print("Backward")
    mlr.MotorSpeedSetAB(s,s)
    mlr.MotorDirectionSet(0b1001)    #0b0101    Rotating in the opposite direction

def leftward(mfb, s):
    #LEFTWARD
    print("Leftward")
    mfb.MotorSpeedSetAB(s,s)
    mfb.MotorDirectionSet(0b0110)    #0b0101    Rotating in the opposite direction

def rightward(mfb, s):
    #RIGHTWARD
    print("RIGHTWARD")
    mfb.MotorSpeedSetAB(s,s)
    mfb.MotorDirectionSet(0b1001)    #0b0101    Rotating in the opposite direction

def stop(mxx):
    #STOP
    print("Stop")
    mxx.MotorSpeedSetAB(0,0)
    time.sleep(1)

try:
    try:
        mfb = grove_i2c_motor_driver.motor_driver(address=0x0f)
        mlr = grove_i2c_motor_driver.motor_driver(address=0x0a)

        #forward(mlr, 50);
        #time.sleep(2);
        while 1:
            time.sleep(0.5)
            gz = gyro.read_data()[2]+40
            print gz
            forward(mlr, lr_s, gz)
            time.sleep(0.1)
            
    except IOError:
        print("Unable to find the motor driver, check the addrees and press reset on the motor driver and try again")
        
    while True:
        try:
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
    stop(mlr)
    stop(mfb)
    sys.exit()
