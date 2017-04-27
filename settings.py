import ConfigParser

from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.popup import Popup
from kivy.core.window import Window
import utils


Builder.load_string("""
<Settings>:
        server_text: _server_text
        size_hint:(None,None)

        GridLayout:
                cols: 1
                padding: '12dp'
                pos: (self.parent.width-self.width)/2, (self.parent.height-self.height)/2
                size_hint: 1, 1



                canvas:
                        Color:
                                rgba: root.background_color[:3] + [root.background_color[-1] * root._anim_alpha]

                        Color:
                                rgb: 1, 1, 1
                        BorderImage:
                                source: root.background
                                border: root.border
                                pos: self.pos
                                size: self.size

                GridLayout:
                        cols: 2
                        Label:
                                text: 'Category'
                                text_size: self.width - dp(16), None
                                halign: 'center'
                        Spinner:
                                id: _server_text
                                values:('192.168.2.16(keuken)', '192.168.2.9(kamer)', '192.168.2.74(studeer)', '192.168.2.12(losse pi)', '192.168.2.124(schuur)', 'localhost(home)')
                                text:'192.168.2.74(studeer)'

                BoxLayout:
                        size_hint_y: 0.5
                        height: sp(48)

                        Button:
                                text: root.cancel_text
                                on_press: root.cancel()
                        Button:
                                text: root.ok_text
                                on_press: root.ok()
""")

path = 'pgp.ini'

servers=('192.168.2.16', '192.168.2.9', '192.168.2.74', '192.168.2.12', '192.168.2.124')

def get_config():
    config = ConfigParser.SafeConfigParser(
        defaults={'mainserver': '192.168.2.74(studeer)'})
    main_server = '192.168.2.74(studeer)'
    config.read(path)
    try:
        main_server = config.get('Servers', 'mainserver')
    except:
        pass
    return {"mainserver": main_server}

def get_available_server():
    for server in servers:
        if utils.ping(server):
            print("server active:"+server)
            return server
    return None

class Settings(Popup):
    server_text = ObjectProperty()

    ok_text = StringProperty('OK')
    cancel_text = StringProperty('Cancel')

    __events__ = ('on_ok', 'on_cancel')

    def __init__(self, change_settings, **kwargs):
        self.size=(Window.width/2,Window.height/2)
        super(Settings, self).__init__(**kwargs)
        self.change_settings = change_settings
        myconfig = get_config()
        self.server_text.text = myconfig["mainserver"]

    def ok(self):
        config = ConfigParser.SafeConfigParser()
        try:
            config.add_section('Servers')
        except:
            pass
        config.set('Servers', 'mainserver', self.server_text.text)
        self.change_settings(self)
        with open(path, "wb") as config_file:
            config.write(config_file)
        self.dispatch('on_ok')
        self.dismiss()

    def cancel(self):
        self.dispatch('on_cancel')
        self.dismiss()

    def on_ok(self):
        pass

    def on_cancel(self):
        pass
