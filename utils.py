import sys

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
    def __init__(self, title, message):
        e = sys.exc_info()[0]
        exc_type, exc_value, exc_traceback = sys.exc_info()
        Alert("Error", text=str(e) + "\n" + str(exc_value) + "\n" + str(exc_traceback))
