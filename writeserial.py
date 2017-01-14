#!/usr/bin/env python 
#sends current status of mpd-player to serial
#mpd must be running
"""
auto-start script if arduino is added:
in file:
/etc/udev/rules.d/90-local.rules
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="2341", ATTR{idProduct}=="0043", RUN+="/usr/bin/python /home/pi/python/writeserial.py"

reload rules:
sudo udevadm control --reload-rules
"""
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

