#!/usr/bin/env python3
"""
ultra_gps_manage.py

Script to control donkey car with GPS navigation. Waypoints are set with GPS coordinates in degrees.

Call: ultra_gps_manage.py -drive
"""

# import GPS Planner and other DK parts
import donkeycar as dk
from gps_parts.gps import GPS
from gps_parts.ultrasonic import Ultrasonic
from gps_parts.ultra_planner import Planner
from donkeycar.vehicle import Vehicle
from donkeycar.parts.actuator import PCA9685, PWMSteering, PWMThrottle

# other important modules
import serial
import pynmea2
import time
import threading


def drive(cfg, goalLocation):
    """
    drive(cfg, goalLocation)

    Add GPS, Planner, and actuator parts and call DK Vehicle.py to run car.
    @param: cfg - configuration file from dk calibration
            goalLocation - list of GPS coordinates in degrees
    @return: None
    """
    # initialize vehicle
    V = Vehicle()

    # GPS is a DK part that will poll GPS data from serial port
    # and output current location in radians.
    gps = GPS(cfg.BAUD_RATE, cfg.PORT, cfg.TIMEOUT)

    # Planner is a DK part that calculates control signals to actuators based on current location
    # from GPS
    planner = Planner(goalLocation=goalLocation, steer_gain=cfg.STEERING_P_GAIN,
                        throttle_gain=cfg.THROTTLE_P_GAIN)

    # Actuators: steering and throttle
    steering_controller = PCA9685(cfg.STEERING_CHANNEL)
    steering = PWMSteering(controller=steering_controller,
                                    left_pulse=cfg.STEERING_LEFT_PWM,
                                    right_pulse=cfg.STEERING_RIGHT_PWM)

    throttle_controller = PCA9685(cfg.THROTTLE_CHANNEL)
    throttle = PWMThrottle(controller=throttle_controller,
                                    max_pulse=cfg.THROTTLE_FORWARD_PWM,
                                    zero_pulse=cfg.THROTTLE_STOPPED_PWM,
                                    min_pulse=cfg.THROTTLE_REVERSE_PWM)

    # add threaded part for gps controller
    V.add(gps, outputs=["currLocation", "prevLocation"], threaded=True)

    #add ultrasonic part. Outputs a stop command if an obstacle is detected
    ultrasonic = Ultrasonic()
    V.add(ultrasonic, outputs=['stop_cmd'], threaded=True)

    # add planner, actuator parts
    V.add(planner, inputs=["currLocation", "prevLocation", "stop_cmd"], outputs=["steer_cmd", "throttle_cmd"])
    V.add(steering, inputs=['steer_cmd'])
    V.add(throttle, inputs=['throttle_cmd'])

    V.start()


if __name__ == '__main__':
    # goalLocation is a list of lists: each sublist a waypoint for the controller.
    
    #this list goes from the Warren lecture halls up to Jacobs
    goalLocation = [[32.881158, -117.234330], [32.881292, -117.234544], [32.881270, -117.235078], [32.881031, -117.235198], [32.881006, -117.235414], [32.881295, -117.235456]]
    
    #this list goes from Jacobs down to the Warren lecture halls
    #goalLocation = [[32.881295, -117.235456], [32.881006, -117.235414], [32.881270, -117.235078], [32.881292, -117.234544], [32.881158, -117.234330]]
    
    cfg = dk.load_config()  
    drive(cfg, goalLocation)
