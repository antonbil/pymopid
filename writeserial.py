#!/usr/bin/env python 
#sends current status of mpd-player to serial
#mpd must be running
"""
auto-start script if arduino is added:

create service to start Arduino
sudo nano /lib/systemd/startArduino.service

[Unit]
Description=Start Arduino Service

[Service]
Type=simple
ExecStart=/home/pi/pymopid/writeserial.py

[Install]
WantedBy=multi-user.target

sudo ln -s /lib/systemd/startArduino.service /etc/systemd/system/startArduino.service

test by:
sudo systemctl start startArduino
sudo systemctl status startArduino

now make rule to start service when usb is plugged in:

in file:
/etc/udev/rules.d/90-local.rules
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="2341", ATTR{idProduct}=="0043", RUN+="/bin/systemctl start startArduino.service"

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

