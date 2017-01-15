import time ## Import 'time' library.  Allows us to use 'sleep' 
import serial
import requests
import mpd
import re
from threading import Thread

class Caroussel:
    def __init__(self,size):
        self.size=size
        self.pad=0
        self.previoustitle=""
    def gettitle(self,title):
        if not self.previoustitle==title:
            self.previoustitle=title
            self.pad=0
        else:
            if len(title)>self.size:
                title=title+"."
                self.pad+=1
                if self.pad>len(title)-1:
                    self.pad=0
                title=title[self.pad:]+title[:self.pad]
        res=title[:self.size].ljust(self.size)
        return res
        

class ConnectArduino:
    def __init__(self,music_controller):
        self.setPort()
        self.line = []
        self.music_controller=music_controller
        self.title_caroussel=Caroussel(16)
        self.artist_caroussel=Caroussel(11)
        self.previoustitle=""
        self.pad=0
        self.sendTitle=False

        
    def exchange(self):
        status=self.music_controller.get_state()
        try:
            t = Thread(target=self.myfunc, args=(status,self.port,))
            t.start()
        except:
            self.setPort()
        return status
    def setPort(self):
        try:
            self.port = serial.Serial("/dev/ttyACM0", baudrate=9600, timeout=0.1, xonxoff=False, rtscts=False, dsrdtr=False)
        except:
            pass

    
    def myfunc(self,status,port):
      try:  
        port.write(status['time1'])
        if self.sendTitle:
            time.sleep(0.1)
            port.write("a"+self.artist_caroussel.gettitle(status['artist']))
            time.sleep(0.2)
            port.write("t"+self.title_caroussel.gettitle(status['title']))
        time.sleep(0.1)
        for c in port.read():
            if c == '\n':
                command="".join(self.line)
                command=re.sub(r'\W+', '', command)

                if command=="Right":
                    self.music_controller.do_action(0)
                if command=="Left":
                    self.music_controller.do_action(3)
                if command=="Title":
                    self.sendTitle=True
                #print("Line: " + command+".")
                self.line = []
                break
            else:
                self.line.append(c)
      except:
        pass
