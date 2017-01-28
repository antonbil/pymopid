import os
import random
import subprocess
from itertools import islice

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.treeview import TreeViewLabel, TreeView

# Remove the specified $song numbers (starting from 0) from the current playlist. No return value.

Builder.load_string("""
<TreeViewLabelB>:
  bcolor: 1, 1, 1, 1
  canvas.before:
    Color:
      rgba: self.bcolor
    Rectangle:
      pos: self.pos
      size: self.size
""")


class TreeViewLabelB(TreeViewLabel):
    bcolor = ListProperty([1, 1, 1, 1])


class TreeWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(TreeWidget, self).__init__(**kwargs)
        self.selected = None
        self.items = []
        # self.on_touch_down=self.touch

    def populate_tree_view(self, tree_view, parent, node):
        if parent is None:
            tree_node = tree_view.add_node(TreeViewLabel(text=node['node_id'], on_touch_up=self.touch1,
                                                         is_open=True,
                                                         font_size=25, ))  # ,bcolor=random.choice(self.colors)
            tree_node.item = node["item"]
            self.items.append(tree_node)
        else:
            tl = TreeViewLabel(text=node['node_id'],
                               is_open=False, font_size=25, )  # ,bcolor=random.choice(self.colors)
            tl.item = node["item"]
            tree_node = tree_view.add_node(tl, parent)

        for child_node in node['children']:
            self.populate_tree_view(tree_view, tree_node, child_node)

    def define(self, tree1, callback, colors):
        self.callback = callback
        self.colors = colors

        self.tv = TreeView(root_options=dict(text='Playlists'),
                           hide_root=True, on_touch_down=self.touch2,
                           indent_level=10)
        self.tv.size_hint = 1, None
        self.tv.bind(minimum_height=self.tv.setter('height'))
        self.populate_tree_view(self.tv, None, tree1)
        root = ScrollView(pos=(0, 0))
        root.add_widget(self.tv)
        self.add_widget(root)

    def touch1(self, instance, touch):
        return False

    def touch2(self, instance, touch):
        """
        Handle a touch event on a child TreeViewLabel

        :param args:
        :param kwargs:
        :return:
        """
        node = self.tv.get_node_at_pos(touch.pos)
        if not node:
            return
        try:
            self.callback(node.item["uri"], node.text)
            return True
        except:
            pass
        self.tv.toggle_node(node)
        node.dispatch('on_touch_down', touch)
        return True


class MeasureButtonOnTouch(Button):
    # this one actually only works on release rather than on press. uses only a
    # time delta

    global go

    def __init__(self, **kwargs):
        super(MeasureButtonOnTouch, self).__init__(**kwargs)
        # self.bind(on_press=self.on_press1)

    def on_press(self, *args):
        global go
        go = True
        Clock.schedule_once(self.menu, 0.5)

    def on_release(self, *args):
        global go
        if go:
            self.onShortPress(self, *args)
        go = False

    def menu(self, *args):
        global go
        if go:
            go = False
            if hasattr(self, 'onLongPress'):
                self.onLongPress(self)
            else:
                # see if popup is needed

                box = BoxLayout()
                popup = Popup(title='test', content=box, size_hint=(0.5, 0.5))
                but = Button(text='Press Dismiss, every once in a while it does not work.\nTry to swipe regardless...',
                             size_hint=(1, None))
                but.bind(on_press=popup.dismiss)
                box.add_widget(but)
                popup.open()


def nth(iterable, n, default=None):
    "Returns the nth item or a default value"
    return next(islice(iterable, n, None), default)


def run_command(command):
    "Returns output after command has been executed in an iteration"
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    return iter(p.stdout.readline, b'')


def contextMenu(buttons, instance, colors, text=None):
    menu = BoxLayout(
        # size_hint=(None, None),
        orientation='vertical')
    if text == None:
        title = "Menu"
    else:
        title = text
    popup = Popup(title=title, content=menu, size=(Window.width/2, (Window.height/8+5) * len(buttons)), size_hint=(None, None))
    for item1 in buttons:
        btn1 = Button(text=item1[0], id="0",
                      background_color=random.choice(colors), size=(Window.width/2-40, Window.height/8))
        btn1.bind(on_release=item1[1])
        btn1.item = instance
        btn1.popup = popup
        menu.add_widget(btn1)
    popup.open()


maxalbums = 120


class SelectMpdAlbum:
    currentdir = ""

    def __init__(self, music_controller, colors, popupSearch, parent, getdir, is_directory, playdir, currentdir=None,
                 addAndPlayAlbum=None, savePlaylist=None):
        # getdir=self.music_controller.mc.list_files(tempdir)
        # def my_condition(self, x):
        #    return "directory" in x
        #            self.playDir(tempdir)


        if addAndPlayAlbum == None:
            self.addAndPlayAlbum = self.addAndPlayMpdAlbum
        else:
            self.addAndPlayAlbum = addAndPlayAlbum
        if not currentdir == None:
            self.currentdir = currentdir
        self.savePlaylist = savePlaylist

        print(self.currentdir)
        self.is_directory = is_directory
        self.playdir = playdir
        self.getdir = getdir
        self.parent = parent
        self.music_controller = music_controller

        self.popupSearch = popupSearch
        self.colors = colors
        self.sortlist = True
        self.layout_popup = GridLayout(cols=1, spacing=10, size_hint_y=None, size=(Window.width/2, Window.height))
        self.layout_popup.bind(minimum_height=self.layout_popup.setter('height'))

        root = ScrollView(size_hint=(1, None), size=(Window.width/2-40, Window.height -Window.height/6), scroll_timeout=250)
        root.add_widget(self.layout_popup)
        grid = BoxLayout(orientation='vertical', size=(
            Window.width/2-20, Window.height - 20))  # (cols=1, spacing=10, size_hint_y=None, size=(400, Window.height))
        grid.add_widget(root)
        self.horizon = BoxLayout(orientation='horizontal', size=(Window.width/2-40, Window.height/8))
        self.horizons = []
        for i in range(5):
            btn1 = Button(text="" + str(i * maxalbums), size=(Window.width/2-60, Window.height/8),background_color=random.choice(self.colors))
            btn1.bind(on_press=lambda x: self.onHorizon(x))
            self.horizons.append(btn1)

            self.horizon.add_widget(btn1)
        grid.add_widget(self.horizon)
        self.popup = Popup(title="", separator_height=0, content=grid, size_hint=(None, None),
                           size=(Window.width/2, Window.height))
        i = 0
        self.buttons = []
        # self.dummies=[]
        for i in range(maxalbums):
            btn1 = MeasureButtonOnTouch(text="", id=str(i), size_hint_y=None, valign='middle', text_size=(Window.width/2-100, None),
                                        halign='left', size=(Window.width/2-60, Window.height/8), 
                                        padding_y=0, background_color=random.choice(self.colors))
            # btn1.bind(on_press=lambda x: self.onClick(x))
            btn1.onShortPress = self.onClick
            btn1.onLongPress = self.onLongClick
            self.buttons.append(btn1)
            # self.dummies.append(self.dummybutton(btn1))
        self.close_button = Button(text="..", id="a", size_hint_y=None, size=(Window.width/2, Window.height/8), on_press=self.goback,
                                   background_color=random.choice(self.colors))
        # self.dummybutton=self.dummybutton()

    def onLongClick(self, instance):  # cab be removed double declaration
        # print("longclick"+instance.text)
        self.playDir(self.currentdir)

    def goback(self, instance):
        # print ("go back")
        head, tail = os.path.split(self.currentdir)
        head, tail = os.path.split(head)
        print(head)
        self.currentdir = head + "/"
        self.display("")

    def playDir(self, dir):
        if dir[-1:] == "/":
            dir = dir[:-1]
        try:
            self.playdir(dir)
        except:
            pass

    def onHorizon(self, instance):
        self.display("", int(instance.text))

    def onClick(self, instance):
        self.display(instance.text + "/")

    def onLongClick(self, instance):
        buttons = [["Add", self.addAlbum], ["Add and Play", self.addAndPlayAlbumCall], ["Spotify", self.albumSpotify],
                   ["Similar", self.similarSpotify]]
        if not self.savePlaylist == None:
            buttons.append(["Save Playlist", self.savePlaylist])
        contextMenu(buttons, instance, self.colors)

    def similarSpotify(self, instance):
        instance.popup.dismiss()
        temp = instance.item.text
        temp = temp.split("-")[0].strip().lower()
        temp1 = self.music_controller.do_mopidy_search(temp)
        temp = temp1[0]['tracks'][0]['artists'][0]['uri'].replace("spotify:artist:", "")
        self.parent.displaySimilarArtists(temp)

    def albumSpotify(self, instance):
        instance.popup.dismiss()
        # print ("add",instance.item.text)
        temp = instance.item.text
        temp = temp.split("-")[0].strip().lower()
        self.popupSearch.artist = temp
        self.popupSearch.display_tracks(temp)

    def addAlbum(self, instance):
        instance.popup.dismiss()
        # print ("add",instance.item.text)
        tempdir = self.currentdir + instance.item.text
        self.playDir(tempdir)

    def addAndPlayAlbumCall(self, instance):
        instance.popup.dismiss()
        tempdir = self.currentdir + instance.item.text
        self.addAndPlayAlbum(tempdir)

    def addAndPlayMpdAlbum(self, tempdir):
        song_pos = self.music_controller.get_length_playlist_mpd()
        self.playDir(tempdir)
        self.music_controller.select_and_play_mpd(song_pos)

    def optionButton(self, instance):
        try:
            tempdir = self.currentdir + instance.prevButton.text
            self.playDir(tempdir)
            # print (instance.prevButton.text)
        except:
            pass

    def dummybutton(self, prevbutton=None):
        btn1 = Button(text="+", id="a", size_hint_y=None, text_size=(40, None), halign='center', valign='middle',
                      size_hint_x=None, size=(45, None), background_color=random.choice(self.colors))
        btn1.prevButton = prevbutton
        btn1.bind(on_press=lambda x: self.optionButton(x))
        return btn1

    def display(self, dir, start=None):
        """display dir, with start"""
        if start == None:
            # self.popupOpen=False
            start = 0
        # print(self.music_controller.mc.list_files(dir))
        tempdir = (self.currentdir + dir).replace("//", "/")
        playlist = self.getdir(tempdir)
        try:
            numdirs = sum(1 for x in playlist if self.is_directory(x))
        except:
            numdirs = 0
        if numdirs == 0:
            print("play:" + tempdir)
            self.playDir(tempdir)
            return

        self.currentdir = tempdir
        self.layout_popup.clear_widgets()
        self.horizon.clear_widgets()
        numbuttons = numdirs / maxalbums + 1
        if numbuttons > 1:
            for i in range(numbuttons):
                self.horizon.add_widget(self.horizons[i])
        i = 0
        self.layout_popup.add_widget(self.close_button)
        # self.layout_popup.add_widget(self.dummybutton)
        if self.sortlist:
            playlist.sort(key=lambda k: ("directory" not in k, k.get("directory", None)))
        i = 0
        for item in playlist:
            if "directory" in item and i >= start and i < maxalbums + start:
                index = i - start
                self.buttons[index].text = item["directory"]
                self.buttons[index].background_color = random.choice(self.colors)
                # self.dummies[index].background_color=random.choice(self.colors)
                self.layout_popup.add_widget(self.buttons[index])
                # self.layout_popup.add_widget(self.dummies[index])
            i += 1

        if not self.popupOpen:
            self.popup.open()
        self.popupOpen = True
