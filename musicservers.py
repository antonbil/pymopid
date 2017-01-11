import difflib
import json
import mpd
import os
import random
import subprocess
from itertools import islice

import requests
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

mpdServerUrl = "192.168.2.74"


class mpd_controller:
    def __init__(self):
        self.client = mpd.MPDClient()

        try:
            self.client.connect(mpdServerUrl, 6600)
        except mpd.ConnectionError:
            pass

            # self.client.disconnect()

    def get_client(self):
        try:
            # self.client.connect(mpdServerUrl, 6600)
            pass
        except mpd.ConnectionError:
            pass
        return self.client

    def release_client(self):
        try:
            self.client.disconnect()
        except mpd.ConnectionError:
            print "can't disconnect"

    def get_status(self):
        mpd_status = self.get_client().status()
        # print "status = " + str(mpd_status)
        # self.release_client()
        volume = (int(mpd_status['volume']) - 80) / 2
        currentsong = self.get_client().currentsong()
        numbers = currentsong["track"].rsplit('/', 1)
        track = int(numbers[0])  # current track
        try:
            totaltracks = int(numbers[1])  # total tracks
        except:
            totaltracks = 0
        # print "currentsong = " + str(currentsong)
        # self.release_client()
        try:
            elapsed = int(mpd_status['elapsed'][:-4])
        except:
            elapsed = 0
        return {'status': mpd_status['state'],
                'elapsed': elapsed,
                'totaltime': int(currentsong["time"]), 'track': track,
                'totaltracks': totaltracks, 'title': currentsong['title'],
                'artist': currentsong['artist'], 'file': currentsong['file'],
                'album': currentsong['album'], 'mode': 'mpd'}

    def play(self, songpos=None):
        if songpos == None:
            self.get_client().play()
        else:
            self.get_client().play(songpos)

    def next(self):
        self.get_client().next()

    def pause(self):
        self.get_client().pause(1)

    def stop(self):
        self.get_client().stop()

    def previous(self):
        self.get_client().previous()

    def clear_tracks(self):
        self.get_client().clear()

    def playlist(self):
        return self.get_client().playlistinfo()

    def list_files(self, uri):
        return self.get_client().listfiles(uri)

    def add(self, uri):
        return self.get_client().add(uri)

    def remove_track(self, songpos):
        return self.get_client().delete(songpos)

    def list_artists(self):
        return self.get_client().list("artist")
        # $pl->delete( $song [, $song [...] ] );


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
    popup = Popup(title=title, content=menu, size=(200, 100 * len(buttons)), size_hint=(None, None))
    for item1 in buttons:
        btn1 = Button(text=item1[0], id="0",
                      background_color=random.choice(colors), size=(200, 50))
        btn1.bind(on_release=item1[1])
        btn1.item = instance
        btn1.popup = popup
        menu.add_widget(btn1)
    popup.open()


class music_controller:
    mc = mpd_controller()

    nl = "2"

    def __init__(self):
        # self.mc = mpd_controller()
        # print ("mc defined")
        self.mpdswitcher = {
            0: self.mc.previous,
            1: self.mc.pause,
            2: self.mc.play,
            3: self.mc.next,
        }

        self.mopidyswitcher = [
            "previous",
            "pause",
            "play",
            "next",
        ]

        self.engine = "mpd"
        self.listArtists = self.getArtists()

    def do_param_mopidy_call(self, method, params=None):
        data = {"jsonrpc": "2.0", "id": 1, "method": method}
        if not params == None:
            data["params"] = params
        headers = {'content-type': 'application/json'}
        url = 'http://' + mpdServerUrl + ':6680/mopidy/rpc'
        # url = 'http://192.168.2.74:6680/mopidy/rpc'

        data1 = json.dumps(data)
        res = requests.post(url, data=data1, headers=headers).json()
        return res

    def play_mopidy(self, songpos):
        try:
            playlist = self.do_mopidy_call("core.tracklist.get_tl_tracks")
            item = playlist[songpos]
            self.do_param_mopidy_call("core.playback.play", {'tlid': item["tlid"]})
        except:
            pass

    def playlist_add_mopidy(self, song):
        print ("add:" + song)
        self.do_param_mopidy_call("core.tracklist.add", {'uris': [song]})

    def play(self, songpos):
        if self.engine == "mpd":
            self.mc.play(songpos)
        else:
            self.play_mopidy(songpos)
            # response = self.do_mopidy_call("core.playback.change_track")

    def browse_mopidy(self, uri):
        # core.library.browse(uri)
        res = self.do_param_mopidy_call("core.library.browse", {'uri': uri})
        print(res)

    def get_length_playlist_mpd(self):
        return len(self.mc.playlist())

    def get_length_playlist_mopidy(self):
        return len(self.get_mopidy_playlist())

    def get_length_playlist(self):
        if self.engine == "mpd":
            return self.get_length_playlist_mpd()
        else:
            return self.get_length_playlist_mopidy()

    def playlist(self):
        if self.engine == "mpd":
            list = self.mc.playlist()

            playlist = []
            for item in list:
                try:
                    m, s = divmod(int(item['time']), 60)
                    t = int(item["track"].rsplit('/', 1)[0])
                    text = '{t:02d}-{artist}-{title}({f:02d}:{s:02d})'.format(f=m, s=s, t=t, artist=item["artist"],
                                                                              title=item["title"])
                    playlist.append(text)
                except:  # catch *all* exceptions
                    pass
            return playlist
        else:
            response = self.get_mopidy_playlist()
            playlist = []
            for item in response:
                m, s = divmod(item["length"] / 1000, 60)
                # track_no
                t = item["track_no"]
                text = '{t:02d}-{artist}-{title}({f:02d}:{s:02d})'.format(f=m, s=s, t=t,
                                                                          artist=item["artists"][0]["name"].encode(
                                                                              'utf-8'),
                                                                          title=item["name"].encode('utf-8'))
                playlist.append(text)
            return playlist

    def do_mopidy_call(self, mopidyaction):
        data = {"jsonrpc": "2.0", "id": 1, "method": mopidyaction}
        headers = {'content-type': 'application/json'}
        url = 'http://' + mpdServerUrl + ':6680/mopidy/rpc'
        # url = 'http://192.168.2.74:6680/mopidy/rpc'

        data1 = json.dumps(data)
        return requests.post(url, data=data1, headers=headers).json()["result"]

    def get_mopidy_playlists(self, instance=None):
        result = self.do_mopidy_call("core.playlists.as_list")
        # print(result)
        return result

    def do_mopidy_similar(self, artist):
        url = "https://api.spotify.com/v1/artists/" + artist + "/related-artists"
        res = requests.get(url).json()
        return res

    def do_mopidy_search(self, artist):
        # mopidy.backend.library.search
        data = {"jsonrpc": "2.0", "id": 1, "params": {'query': {'artist': [artist]}}, "exact": "True",
                "method": "core.library.search"}
        headers = {'content-type': 'application/json'}
        url = 'http://' + mpdServerUrl + ':6680/mopidy/rpc'
        # url = 'http://192.168.2.74:6680/mopidy/rpc'

        data1 = json.dumps(data)
        res = requests.post(url, data=data1, headers=headers).json()
        return res["result"]

    def clear_tracks(self, instance=None):
        if self.engine == "mpd":
            self.mc.clear_tracks()

        else:
            # core.tracklist.clear
            self.do_mopidy_call("core.tracklist.clear")

    def do_action(self, action):
        if action == 4:
            # App.get_running_app().stop()
            return  # menu-button
        # print("engine is now:"+self.engine)
        # print(self.do_mopidy_search("Eagles"))
        # return
        if self.engine == "mpd":
            # Get the function from switcher dictionary
            func = self.mpdswitcher.get(action, lambda: "nothing")
            func()
        else:
            # do nothing
            todo = self.mopidyswitcher[action]
            response = self.do_mopidy_call("core.playback." + todo)
        return

    def get_mopidy_playlist(self):
        return self.do_mopidy_call("core.tracklist.get_tracks")

    def remove_track_mopidy(self, songpos):
        tracklist = self.get_mopidy_playlist()
        uri = tracklist[songpos]["uri"]
        self.do_param_mopidy_call("core.tracklist.remove", {'criteria': {"uri": [uri]}})

    def remove_track(self, songpos):
        if self.engine == "mpd":
            # Get the function from switcher dictionary
            self.mc.remove_track(songpos)
        else:
            self.remove_track_mopidy(songpos)

    def switch(self):
        if self.engine == "mpd":
            self.select_and_play_mopidy(0)
            # self.do_mopidy_call("core.playback.play")
        else:
            self.select_and_play_mpd(0)

    def select_and_play_mopidy(self, song_pos):
        self.do_mopidy_call("core.playback.stop")
        self.mc.stop()
        self.engine = 'mopidy'
        self.play_mopidy(song_pos)

    def select_and_play_mpd(self, song_pos):
        self.do_mopidy_call("core.playback.stop")
        self.mc.stop()
        self.engine = 'mpd'
        self.mc.play(song_pos)

    def getArtists(self):
        s = self.mc.list_artists()
        s = [item.lower() for item in s]
        return s

    def find_artist(self, search):
        search = search.lower()
        # no_integers = [x for x in s if len(x)>0]
        # print(no_integers)
        res = difflib.get_close_matches(search, self.listArtists, 25)
        print (res)
        find = res[0]
        for item in res:
            if search in item:
                find = item
        return (res, find)

    def get_state(self):
        status = {}
        time1 = "0000"
        try:
            status = self.mc.get_status()  # mpd_controller
            if status["status"] == 'play':
                m, s = divmod(status["elapsed"], 60)
                if 0 < s % 10 < 3:
                    time1 = '{f:02d}{s:02d}'.format(f=int(status["track"]), s=int(status["totaltracks"]))
                else:
                    time1 = '{f:02d}{s:02d}'.format(f=m, s=s)
                self.engine = "mpd"
            else:
                raise Exception('mpd not playing')
        except:  # catch *all* exceptions
            # e = sys.exc_info()[0]
            # print( e )
            # exc_type, exc_value, exc_traceback = sys.exc_info()
            # print repr(traceback.extract_tb(exc_traceback))
            try:
                # no music playing on mpd
                # try to get data from mopidy
                response = self.do_mopidy_call("core.playback.get_time_position")

                seconds = response / 1000
                m, s = divmod(seconds, 60)

                result = self.do_mopidy_call("core.playback.get_current_track")
                # print(result)
                try:
                    track = (result["track_no"])
                except:
                    track = 0
                try:
                    artist = result["artists"][0]["name"]
                except:
                    artist = ""
                try:
                    album = result["album"]["name"]
                except:
                    album = ""
                try:
                    name = result["name"]
                except:
                    name = ""
                try:
                    uri = result["album"]["uri"]
                except:
                    uri = ""
                try:
                    totaltime = int(result["length"]) / 1000
                except:
                    totaltime = 0
                status = {'status': 'play', 'elapsed': seconds, 'totaltime': totaltime, 'track': track,
                          'totaltracks': 0, 'title': name, 'artist': artist, 'file': uri, 'album': album,
                          'mode': 'mopidy'}
                self.engine = "mopidy"
                if 0 < s % 10 < 3:
                    time1 = '{f:02d}{s:02d}'.format(f=track, s=0)
                else:
                    # display current time
                    time1 = '{f:02d}{s:02d}'.format(f=m, s=s)
            except:  # catch *all* exceptions
                time1 = "0000"
                # e = sys.exc_info()[0]
                # print( e )
                # exc_type, exc_value, exc_traceback = sys.exc_info()
                # print repr(traceback.extract_tb(exc_traceback))

        status["time1"] = time1
        return status


maxalbums = 120


class SelectMpdAlbum:
    currentdir = ""

    def __init__(self, music_controller, colors, popupSearch, parent, getdir, is_directory, playdir):
        # getdir=self.music_controller.mc.list_files(tempdir)
        # def my_condition(self, x):
        #    return "directory" in x
        #            self.playDir(tempdir)


        self.is_directory = is_directory
        self.getdir = getdir
        self.parent = parent
        self.music_controller = music_controller

        self.popupSearch = popupSearch
        self.colors = colors
        self.layout_popup = GridLayout(cols=1, spacing=10, size_hint_y=None, size=(400, Window.height))
        self.layout_popup.bind(minimum_height=self.layout_popup.setter('height'))

        root = ScrollView(size_hint=(1, None), size=(400, Window.height - 80), scroll_timeout=250)
        root.add_widget(self.layout_popup)
        grid = BoxLayout(orientation='vertical', size=(
            450, Window.height - 20))  # (cols=1, spacing=10, size_hint_y=None, size=(400, Window.height))
        grid.add_widget(root)
        self.horizon = BoxLayout(orientation='horizontal')
        self.horizons = []
        for i in range(5):
            btn1 = Button(text="" + str(i * maxalbums), background_color=random.choice(self.colors))
            btn1.bind(on_press=lambda x: self.onHorizon(x))
            self.horizons.append(btn1)

            self.horizon.add_widget(btn1)
        grid.add_widget(self.horizon)
        self.popup = Popup(title="", separator_height=0, content=grid, size_hint=(None, None),
                           size=(450, Window.height))
        i = 0
        self.buttons = []
        # self.dummies=[]
        for i in range(maxalbums):
            btn1 = MeasureButtonOnTouch(text="", id=str(i), size_hint_y=None, valign='middle', text_size=(400, 40),
                                        halign='left', size=(400, 45), background_color=random.choice(self.colors))
            # btn1.bind(on_press=lambda x: self.onClick(x))
            btn1.onShortPress = self.onClick
            btn1.onLongPress = self.onLongClick
            self.buttons.append(btn1)
            # self.dummies.append(self.dummybutton(btn1))
        self.close_button = Button(text="..", id="a", size_hint_y=None, size=(400, 45), on_press=self.goback,
                                   background_color=random.choice(self.colors))
        # self.dummybutton=self.dummybutton()

    def onLongClick(self, instance):  #cab be removed double declaration
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
            self.playdir()
        except:
            pass

    def onHorizon(self, instance):
        self.display("", int(instance.text))

    def onClick(self, instance):
        print("select" + instance.text)
        self.display(instance.text + "/")

    def onLongClick(self, instance):
        buttons = [["Add", self.addAlbum], ["Add and Play", self.addAndPlayAlbum], ["Spotify", self.albumSpotify],
                   ["Similar", self.similarSpotify]]
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

    def addAndPlayAlbum(self, instance):
        instance.popup.dismiss()
        song_pos = self.music_controller.get_length_playlist_mpd()
        tempdir = self.currentdir + instance.item.text
        self.playDir(tempdir)
        print("pos:", song_pos)
        self.music_controller.select_and_play_mpd(song_pos)


    def optionButton(self, instance):
        try:
            tempdir = self.currentdir + instance.prevButton.text
            self.playDir(tempdir)
            # print (instance.prevButton.text)
        except:
            pass

    def dummybutton(self, prevbutton=None):
        btn1 = Button(text="+", id="a", size_hint_y=None, text_size=(40, 40), halign='center', valign='middle',
                      size_hint_x=None, size=(45, 45), background_color=random.choice(self.colors))
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
        numdirs = sum(1 for x in playlist if self.is_directory(x))
        if numdirs == 0:
            # print("play:"+tempdir)
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
