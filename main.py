from kivy.app import App
from kivy.config import Config
from basic import LoginScreen
class MyApp(App):
    def build(self):
        return LoginScreen()


if __name__ == '__main__':
    Config.set("kivy", "keyboard_mode", 'systemanddock')
    Config.write()

    MyApp().run() 
