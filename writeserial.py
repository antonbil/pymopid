#!/usr/bin/env python 
#sends current status of mpd-player to serial
#mpd must be running

import time ## Import 'time' library.  Allows us to use 'sleep' 
import connectArduino
import musiccontroller
#start main loop to run every second
music_controller=musiccontroller.music_controller()

arduino=connectArduino.ConnectArduino(music_controller)

while True:
    arduino.exchange()
    time.sleep(1)
port.close()

