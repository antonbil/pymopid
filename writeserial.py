#!/usr/bin/env python 
#sends current status of mpd-player to serial
#mpd must be running, mpc must be installed
import time ## Import 'time' library.  Allows us to use 'sleep' 
import sys, getopt
import serial
import subprocess
from itertools import permutations, islice
import requests
import json, mpd, musiccontroller

#main program
#open serial port
#port = serial.Serial("/dev/ttyACM0", baudrate=9600, timeout=0.8)
port = serial.Serial("/dev/ttyACM0", baudrate=9600, timeout=0.1, xonxoff=False, rtscts=False, dsrdtr=False)
#port = serial.Serial("/dev/ttyACM0", timeout=None, baudrate=115000, xonxoff=False, rtscts=False, dsrdtr=False)
#start main loop to run every second
line = []
music_controller=musiccontroller.music_controller()

while True:
    status=status=music_controller.get_state()

    #print (status)
    port.write(status['title'])
    time.sleep(0.1)
    port.write(status['time1'])
    time.sleep(0.4)
    for c in port.read():
        line.append(c)
        if c == '\n':
            print("Line: " + "".join(line))
            line = []
            break

    #print(time1)
    time.sleep(0.5)
port.close()

