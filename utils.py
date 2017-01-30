import sys
from platform import system as system_name # Returns the system/OS name 
from os import system as system_call # Execute a shell command

from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.popup import Popup


def remove_slash_at_end(s):
    if s[-1:] == "/":
        s = s[:-1]
    return s


def remove_slash_at_start(s):
    if s[:1] == "/":
        s = s[1:]
    return s


class Alert:
    def __init__(self, title, message):
        popup = Popup(title=title, pos_hint={'x': 10.0 / Window.width,
                                             'y': 10.0 / Window.height},
                      content=Label(text=message),  # text= str(e)+"\n"+str(exc_value)+"\n"+str(exc_traceback)),
                      size_hint=(None, None), size=(Window.width / 2, Window.height / 2))
        popup.open()


class AlertError:
    def __init__(self):
        e = sys.exc_info()[0]
        exc_type, exc_value, exc_traceback = sys.exc_info()
        Alert("Error", str(e) + "\n" + str(exc_value) + "\n" + str(exc_traceback))

def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that some hosts may not respond to a ping request even if the host name is valid.
    """

    # Ping parameters as function of OS
    ping_param = "-n 1" if system_name().lower=="windows" else "-c 1"

    # Pinging
    return system_call("ping " + ping_param + " " + host) == 0