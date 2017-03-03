#!/usr/bin/env python
import sys     # exit
import subprocess # for calling shell script
import grovepi # grovepi
import grove_i2c_motor_driver
import itg3200 # library for grove gyroscope
import time    # sleep

# update with your bus number and address
gyro = itg3200.SensorITG3200(1, 0x68)
gyro.default_init()
# pin numbers for ultrasonic rangers # note D14 corresponds to A0
ultrasonic_rangers = (8, 4, 3, 14, 2, 5, 7, 6)
distances = [0] * 8
# + denote clockwise, - denote counter-clockwise
velocities = [1, 1, 1, 1]
speedLimit = 100
s = [100, 100]

# initalize motors and return two motor pairs, 02 and 13
def initMotors():
    # motor driver addresses accordingly
    motors02 = grove_i2c_motor_driver.motor_driver(address=0x0f)
    motors13 = grove_i2c_motor_driver.motor_driver(address=0x0a)
    return motors02, motors13

# set the velocities of the motors with the speedLimit as the fastest speed allowed
def setVelocities((motors02, motors13), velocities, speedLimit):
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
    speedLimit += 0.0
    maxSpeed = max(abs(max(velocities)), abs(min(velocities)))
    if maxSpeed > 0:
        for i in range(4):
            velocities[i] *= speedLimit/maxSpeed

# get the distances from each ultrasonic ranger
def getDistances(ultrasonic_rangers, distances):
    for i in range(len(ultrasonic_rangers)):
        distances[i] = grovepi.ultrasonicRead(ultrasonic_rangers[i])

# get rotation from gyroscope
def getRotation():
    # storing the z-axis gyro value
    return gyro.read_data()[2]+40
# avoid getting hit
def avoidObstacles(distances, velocities):
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
    for i in range(len(distances)):
        if distances[i] > 300:
            velocities[(i/2+1)%4] += (distances[i]-300)/10
            velocities[(i/2+3)%4] -= (distances[i]-300)/10
            # if the ranger is between two motors
            if i%2 == 1:
                velocities[(i/2+2)%4] += (distances[i]-300)/10
                velocities[(i/2+4)%4] -= (distances[i]-300)/10
            break

# stop motors
def stop(motors):
    #STOP
    print("Stop")
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
            print("rotation", rotation)
            # Read distance value from Ultrasonic
            getDistances(ultrasonic_rangers, distances)
            print("distances", distances)
            explore(distances, velocities)
            avoidObstacles(distances, velocities)
            setVelocities(motors, velocities, speedLimit)
            print(velocities)

        except TypeError:
            print ("TypeError")
            subprocess.call(['./avrdude_test.sh'])
        except IOError:
            print ("IOError")
except KeyboardInterrupt: # stop motors before exit
    stop(motors)
    sys.exit()
