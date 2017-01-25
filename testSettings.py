from kivy import Config
from kivy.app import App
from kivy.uix.button import Button

from settings import Settings


class MyApp(App):
    def build(self):
        btn1 = Button(text='test')
        btn1.bind(on_press=self.test)
        return btn1

    def test(self, instance):
        settings = Settings()
        settings.open()


if __name__ == '__main__':
    Config.set("kivy", "keyboard_mode", 'systemanddock')
    Config.write()

    MyApp().run()
