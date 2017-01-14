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
import re
#main program
#open serial port
#port = serial.Serial("/dev/ttyACM0", baudrate=9600, timeout=0.8)
#port = serial.Serial("/dev/ttyACM0", timeout=None, baudrate=115000, xonxoff=False, rtscts=False, dsrdtr=False)
#start main loop to run every second
music_controller=musiccontroller.music_controller()

class ConnectArduino:
    def __init__(self,music_controller):
        self.port = serial.Serial("/dev/ttyACM0", baudrate=9600, timeout=0.1, xonxoff=False, rtscts=False, dsrdtr=False)
        self.line = []
        self.music_controller=music_controller

        
    def exchange(self):
        status=status=music_controller.get_state()

        #print (status)
        self.port.write(status['title'])
        time.sleep(0.02)
        self.port.write(status['time1'])
        time.sleep(0.03)
        for c in self.port.read():
            if c == '\n':
                command="".join(self.line)
                command=re.sub(r'\W+', '', command)

                if command=="Right":
                    self.music_controller.do_action(0)
                if command=="Left":
                    self.music_controller.do_action(3)
                print("Line: " + command+".")
                self.line = []
                break
            else:
                self.line.append(c)


        #print(time1)

arduino=ConnectArduino(music_controller)

while True:
    arduino.exchange()
    time.sleep(0.95)
port.close()

