import os
import random
import serial
import sys
import tempfile
import traceback
from time import sleep

import requests
from BeautifulSoup import BeautifulSoup as bs
from kivy.adapters.dictadapter import ListAdapter
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import *
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.listview import ListView, ListItemButton
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from smb.SMBConnection import SMBConnection

import musicservers
import musiccontroller
import connectArduino
from musicservers import MeasureButtonOnTouch

SAMBA_SERVER = "192.168.2.8"

red = [1, 0, 0, 1]
green = [0, 1, 0, 1]
blue = [0, 0, 1, 1]
purple = [1, 0, 1, 1]
colors = [red, green, blue, purple]

buttons = [["1", "<<"], ["2", "||"], ["3", ">"], ["4", ">>"], ["5", "Menu"], ]


class IconButton(ButtonBehavior, AsyncImage):
    pass


class LabelButton(ButtonBehavior, Label):
    pass


class PopList:
    def __init__(self, maxtracks, getlist, onpopup, process_item, on_long_press=None):
        self.onLongPress = on_long_press
        self.processItem = process_item
        self.onpopup = onpopup
        self.getList = getlist
        self.maxlist = maxtracks
        self.layout_popup = GridLayout(cols=1, spacing=10, size_hint_y=None, size=(400, Window.height), valign="top")
        self.layout_popup.bind(minimum_height=self.layout_popup.setter('height'))
        root = ScrollView(size_hint=(1, None), size=(400, Window.height - 80), scroll_timeout=250, valign="top")
        root.add_widget(self.layout_popup)
        grid = BoxLayout(orientation='vertical', size=(
            450, Window.height - 20))  # (cols=1, spacing=10, size_hint_y=None, size=(400, Window.height))
        grid.add_widget(root)
        self.horizon = BoxLayout(orientation='horizontal')
        self.horizons = []
        for i in range(10):
            btn1 = Button(text="" + str(i * self.maxlist), background_color=random.choice(colors))
            btn1.bind(on_press=self.onHorizon)
            self.horizons.append(btn1)

            self.horizon.add_widget(btn1)
        grid.add_widget(self.horizon)
        self.popup = Popup(title="", separator_height=0, content=grid, size_hint=(None, None),
                           size=(450, Window.height))
        # create buttons so they can be re-used
        self.buttons = []
        for i in range(maxtracks):
            btn1 = MeasureButtonOnTouch(text="", id=str(i), size_hint_y=None, text_size=(400, 40), valign='middle',
                                        halign='left', size=(400, 45), background_color=random.choice(colors))
            btn1.onShortPress = self.mypopup
            btn1.onLongPress = self.longpress

            self.buttons.append(btn1)

    def mypopup(self, instance):
        self.onpopup(instance, instance.nr)

    def longpress(self, instance):
        if self.onLongPress:
            self.onLongPress(instance, instance.nr)

    def display_tracks(self, instance, start=None):
        if start == None:
            self.popupOpened = False
            start = 0
        self.start = start
        self.layout_popup.clear_widgets()
        self.horizon.clear_widgets()

        playlist = self.getList()
        for i in range(len(playlist) / self.maxlist + 1):
            try:
                self.horizon.add_widget(self.horizons[i])
            except:
                pass
        i = 0
        for item in playlist:
            if i >= start and i < self.maxlist + start:
                index = i - start
                self.buttons[index].text = self.processItem(item)
                self.buttons[index].background_color = random.choice(colors)
                self.buttons[index].nr = i
                self.buttons[index].item = item
                self.layout_popup.add_widget(self.buttons[index])
            i += 1

        if not self.popupOpened:
            self.popup.open()
        self.popupOpened = True

    def onHorizon(self, instance):
        # print("select"+instance.text)
        self.display_tracks(instance, int(instance.text))


class MenuScreen(GridLayout):
    def __init__(self, main, **kwargs):
        super(MenuScreen, self).__init__(**kwargs)
        self.main = main
        self.cols = 2
        self.orientation = "vertical"
        self.addButton("Tracks", self.main.popupTracks.display_tracks)
        self.addButton("Clear", self.main.music_controller.clear_tracks)
        self.addButton("Spotify", self.main.listArtistOpen)
        self.addButton("Mpd", self.main.list_files)
        self.addButton("Mpd playlists", self.main.list_smb_files)
        self.addButton("Mpd <--> Spotify", self.main.mpd_spotify)
        self.addButton("Playlists", self.main.popupPlaylists.display_tracks)
        self.addButton("Playlists tree", self.main.display_tracks_tree)
        self.addButton("Spotify playlists", self.main.list_spotify_files)
        self.addButton("Similar artists", self.main.similarForPlayingArtist)
        self.addButton("Quit", self.main.quit)
        self.popup = Popup(title="Menu", content=self, size=(400, 400), size_hint=(None, None))

    def addButton(self, title, action):
        btn = Button(text=title, id="0",
                     background_color=random.choice(colors), size=(200, 50)
                     )
        self.add_widget(btn)
        # btn.onShortPress=action
        btn.bind(on_press=action)
        return btn

    def open(self, instance):
        # open the popup
        self.popup.open()


maxtracks = 30  # max number of tracks displayed in playlist


class ListArtist(GridLayout):
    def __init__(self, **kwargs):
        super(ListArtist, self).__init__(**kwargs)
        self.cols = 2
        self.size = (200, 200)
        # create content and add to the popup
        closeButton = Button(text='OK', size=(100, 50), size_hint=(None, None))
        self.popup = Popup(title="Search artist", content=self, size=(340, 400), size_hint=(None, None),
                           pos_hint={'right': .5, 'top': 1})
        self.add_widget(Label(text="Artist:", size=(100, 50), size_hint=(None, None)))
        self.artist = TextInput(multiline=False, size=(170, 50), size_hint=(None, None))
        self.artist.bind(text=self.on_text)
        self.add_widget(self.artist)
        self.add_widget(closeButton)
        self.suggestButton = Button(text='', size=(200, 50), size_hint=(None, None))
        self.suggestButton.bind(on_press=self.suggest)
        self.list_adapter = ListAdapter(data=[], cls=ListItemButton, sorted_keys=[])
        self.list_adapter.bind(on_selection_change=self.list_changed)
        # list_view = ListView(adapter=self.list_adapter)
        self.list = ListView(adapter=self.list_adapter)
        self.add_widget(self.list)
        # self.add_widget(self.suggestButton)

        # bind the on_press event of the button to the dismiss function
        closeButton.bind(on_press=self.action)

    def list_changed(self, list, *args):
        '''dit is commentaar'''
        self.artist.text = list.selection[0].text

    def open(self, parent, listalbums):
        # open the popup
        self.parent = parent
        self.listalbums = listalbums
        self.popup.open()

    def suggest(self, instance):
        '''dit is  commentaar, wat hoort bij de bovenstaande functie'''
        # close the popup
        self.popup.dismiss()
        '''dit is ander commentaar, wat hoort bij de bovenstaande code'''
        self.listalbums.artist = self.suggestButton.text
        self.listalbums.display_tracks(self.artist.text)

    def action(self, instance):
        # close the popup
        self.popup.dismiss()
        # print ("search artist:"+self.artist.text)
        self.listalbums.artist = self.artist.text
        self.listalbums.display_tracks(self.artist.text)

    def on_text(self, instance, value):
        print("find:" + value, self.parent)
        try:
            # print("find:"+value,self.parent.music_controller)
            list, find = self.parent.music_controller.find_artist(value)
            list.sort(key=lambda x: 0 if value in x else 1)
            # a if condition else b
            self.suggestButton.text = find
            self.list_adapter.data = list
            # print('suggest:', find)
        except:
            pass


Builder.load_string('''
<ScrollableLabel>:
    Label:
        size_hint_y: None
        height: self.texture_size[1]
        font_size:'50sp'
        multiline:True
        markup:True
        text_size: self.width, None
        text: root.text
''')


class ScrollableLabel(ScrollView):
    text = StringProperty('')

    def __init__(self, **kwargs):
        super(ScrollableLabel, self).__init__(**kwargs)


Builder.load_string("""
<PopupBox>:
    pop_up_text: _pop_up_text
    size_hint: .5, .5
    auto_dismiss: True
    title: 'Status'   

    BoxLayout:
        orientation: "vertical"
        Label:
            id: _pop_up_text
            text: ''
""")


class PopupBox(Popup):
    pop_up_text = ObjectProperty()

    def update_pop_up_text(self, p_message):
        self.pop_up_text.text = p_message


class SmbDir:
    def __init__(self):
        self.conn = SMBConnection("wieneke", "wieneke", "client", "", use_ntlm_v2=True)
        assert self.conn.connect(SAMBA_SERVER, 139)

    def get_dir(self, dir):
        pathlist = self.conn.listPath("FamilyLibrary", dir, search=55, pattern='*', timeout=30)
        list = []
        for path in pathlist:
            if path.filename[:1] == ".":
                continue
            if path.isDirectory:
                path.directory = path.filename
                list.append({'filename': path.filename, 'directory': path.directory})
            else:
                list.append({'filename': path.filename})
        return list

    def get_content_file(self, filename):
        file_obj = tempfile.NamedTemporaryFile()
        with open('local_file', 'wb') as fp:
            self.conn.retrieveFile('FamilyLibrary', filename, fp)
        return [line.rstrip('\n') for line in open('local_file')]


class SpotifyPlaylist:
    def __init__(self, music_controller):
        self.music_controller = music_controller

    def play_mopidy_playlist(self, url):
        parts = url.split("/")
        last = parts[len(parts) - 1]
        self.music_controller.playlist_add_mopidy(self.mopidy_playlists[last])

    def get_mopify_playlist(self, url):
        response = requests.get("http://" + url)
        soup = bs(response.content)
        list = []
        for link in soup.findAll('a'):
            if "/" in link['href'] and not "Parent" in link.string:
                list.append({'filename': link.string, 'directory': link.string})
        if len(list) == 0:
            self.myurls = soup.findAll("div", {"class": "url"})
            myartists = soup.findAll("div", {"class": "artist"})
            myalbums = soup.findAll("div", {"class": "album"})
            if len(myalbums) == 0:
                return []
            i = 0
            self.mopidy_playlists = {}
            for artist in myartists:
                text = artist.text + "-" + myalbums[i].text
                self.mopidy_playlists[text] = self.myurls[i].text
                list.append({'filename': text, 'directory': text, "url": self.myurls[i].text})
                i += 1
        return list

    def addAndPlaySpotifyAlbum(self, tempdir):
        song_pos = self.music_controller.get_length_playlist_mopidy()
        self.play_mopidy_playlist(tempdir)
        self.music_controller.select_and_play_mopidy(song_pos)


class LoginScreen(BoxLayout):
    image_source = ObjectProperty()
    previousimage = ""
    music_controller = 0
    mode_title = True

    def __init__(self, **kwargs):
        self.smb_dir = SmbDir()
        self.smb_dir.get_dir("TotalMusic")

        self.music_controller = musiccontroller.music_controller()
        self.arduino=connectArduino.ConnectArduino(music_controller)

        super(LoginScreen, self).__init__(**kwargs)
        self.orientation = "vertical"

        h_layout0 = BoxLayout(padding=10, size_hint=(1.0, 0.2))
        for i in range(5):
            btn = Button(text=buttons[i][1], id=buttons[i][0],
                         background_color=random.choice(colors), size=(100, 50)
                         )
            buttons[i].append(btn)
            btn.bind(on_press=self.doAction)

            h_layout0.add_widget(btn)

        # define popup for tracks
        self.popupTracks = PopList(maxtracks, self.getTracks, self.onSelectTrackAction, self.processItem,
                                   self.onLongpressTrack)
        self.popupPlaylists = PopList(80, self.getPlaylists, self.onSelectPlaylistAction, self.processPlaylist,
                                      self.onLongpressPlaylist)
        self.popupSearch = PopList(maxtracks, self.getSearch, self.onSelectSearchAction, self.processSearch,
                                   self.onLongpressSearch)
        self.similarArtistsPopup = PopList(maxtracks, self.getsimilarArtistsPopup, self.onSelectsimilarArtistsPopup,
                                           self.processsimilarArtistsPopup, self.onLongpresssimilarArtistsPopup)
        self.listArtist = ListArtist()
        self.menuScreen = MenuScreen(self)
        self.menuScreen.main = self
        buttons[4][2].bind(on_release=self.menuScreen.open)
        v_layout = BoxLayout(padding=10)
        v_layout.orientation = "vertical"
        h_layout1 = BoxLayout(padding=10)
        h_layout2 = BoxLayout(padding=10)

        self.label = ScrollableLabel(size_hint=(1, None), size=(400, 250))

        v_layout.add_widget(self.label)
        h_layout1.add_widget(v_layout)
        # sudo kate  /usr/lib/python2.7/dist-packages/kivy/core/image/img_pil.py regel 86, verander img_tmp.mode.lower(), img_tmp.tostring()) , tostring()in tobytes()
        self.image_source = IconButton(allow_stretch=True)

        h_layout1.add_widget(self.image_source)
        self.time = Label(font_size='45sp')
        h_layout2.add_widget(self.time)
        self.tracknr = Label(font_size='45sp')
        h_layout2.add_widget(self.tracknr)
        self.totaltime = LabelButton(font_size='45sp')
        # self.totaltime.bind(on_release=self.listArtistOpen )
        self.totaltime.bind(on_press=self.mode_title)
        h_layout2.add_widget(self.totaltime)
        v_layout.add_widget(h_layout2)
        self.add_widget(h_layout0)
        self.add_widget(h_layout1)
        # list to select albums to play
        self.selAlbum = musicservers.SelectMpdAlbum(self.music_controller, colors, self.popupSearch, self,
                                                    getdir=lambda x: self.music_controller.mc.list_files(x),
                                                    is_directory=lambda x: "directory" in x,
                                                    playdir=lambda x: self.music_controller.mc.add(x[1:]))
        spotify_playlist = SpotifyPlaylist(self.music_controller)
        self.selMopidyAlbum = musicservers.SelectMpdAlbum(self.music_controller, colors, self.popupSearch, self,
                                                          getdir=lambda x: spotify_playlist.get_mopify_playlist(x),
                                                          is_directory=lambda x: "directory" in x,
                                                          playdir=lambda x: spotify_playlist.play_mopidy_playlist(x),
                                                          currentdir="192.168.2.8/spotify/data",
                                                          addAndPlayAlbum=spotify_playlist.addAndPlaySpotifyAlbum)
        self.selSmbAlbum = musicservers.SelectMpdAlbum(self.music_controller, colors, self.popupSearch, self,
                                                       getdir=lambda x: self.smb_dir.get_dir(x),
                                                       is_directory=lambda x: "directory" in x,
                                                       playdir=lambda x: self.play_samba_dir(x),
                                                       currentdir="TotalMusic")
        Clock.schedule_interval(self.update, 1)

    def list_spotify_files(self, instance):
        self.selMopidyAlbum.popupOpen = False
        self.selMopidyAlbum.display("/")
    def play_samba_dir(self, dir):
        filename = dir + "/mp3info.txt"
        lines = self.smb_dir.get_content_file(filename)
        del lines[0]
        for item in lines:
            fname = item.split("=== ")[0].replace("/home/wieneke/FamilyLibrary/FamilyMusic/", "")
            self.music_controller.mc.add(fname)

    def display_tracks_tree(self, instance=None):
        try:
            self.popupPlaylists.open()
        except:
            print("long running task")
            self.show_popup()
            print("long running task2")
            lists = self.getPlaylists()
            tree = {'node_id': 'root', 'item': None,
                    'children': []}
            root = tree['children']
            for item in lists:
                name = item["name"].split("/")
                last = name[-1]
                subroot = root
                for part in name:
                    equal = False
                    for t in subroot:
                        if t['node_id'] == part:
                            equal = True
                            subroot = t['children']
                    if not equal:
                        t1 = {'node_id': part,
                              'children': [], 'item': None}
                        subroot.append(t1)
                        if part == last:
                            t1["item"] = item
                        else:
                            t1["item"] = None
                        subroot = t1['children']

            tw = musicservers.TreeWidget()
            tw.define(tree, self.playlistTreeCallback, colors)
            self.popupPlaylists = Popup(title="", separator_height=0, content=tw, size_hint=(None, None),
                                        size=(600, Window.height))
            self.pop_up.dismiss()

            self.popupPlaylists.open()

    def show_popup(self):
        self.pop_up = PopupBox()
        self.pop_up.update_pop_up_text('Running some task...')
        self.pop_up.open()

    def popupPlaylistsToNone(self):
        self.popupPlaylists = None

    def playlistTreeCallback(self, uri, text=None):
        song_pos = self.music_controller.get_length_playlist_mopidy()
        buttons = [["Add", lambda x: self.music_controller.playlist_add_mopidy(uri)]
            , ["Add and Play", lambda x: [None,
                                          self.music_controller.playlist_add_mopidy(uri),
                                          sleep(1),
                                          self.music_controller.select_and_play_mopidy(song_pos)
                                          ][0]],
                   ["Reread playlists", lambda x:
                   [None, self.popupPlaylists.dismiss(), self.popupPlaylistsToNone(), self.display_tracks_tree()
                    ][0]
                    ]
                   ]
        instance = None
        musicservers.contextMenu(buttons, instance, colors, text)
        # self.music_controller.playlist_add_mopidy(uri)

    def listArtistOpen(self, instance):
        # print("list artist open")
        self.listArtist.open(self, self.popupSearch)

    # following necessary for popupPlaylists
    def getPlaylists(self):
        return self.music_controller.get_mopidy_playlists()

    def processPlaylist(self, item):
        # item an be changed if it is an object
        return item["name"]

    def onSelectPlaylistAction(self, instance, start):
        self.music_controller.playlist_add_mopidy((instance.item["uri"]))

    # following necessary for popupTracks
    def getTracks(self):
        return self.music_controller.playlist()

    def processItem(self, item):
        # item an be changed if it is an object
        return item

    def onLongpressTrack(self, instance, nr):
        buttons = [["Remove track", self.remove_track], ["Remove top", self.remove_top],
                   ["Remove bottom", self.remove_bottom]]
        musicservers.contextMenu(buttons, instance, colors)

    def remove_track(self, instance):
        instance.popup.dismiss()
        # self.music_controller.find_artist("Sola")
        # self.music_controller.browse_mopidy("spotify:")
        self.music_controller.remove_track(instance.item.nr)

    def remove_top(self, instance):
        instance.popup.dismiss()
        for i in range(instance.item.nr):
            self.music_controller.remove_track(0)

    def remove_bottom(self, instance):
        instance.popup.dismiss()
        len = self.music_controller.get_length_playlist()
        for i in range(instance.item.nr, len):
            self.music_controller.remove_track(instance.item.nr)

    def onLongpressPlaylist(self, instance, pos):
        buttons = [["Add", self.addPlaylist], ["Add and Play", self.addAndPlayPlaylist]]
        musicservers.contextMenu(buttons, instance, colors)

    def addPlaylist(self, instance):
        instance.popup.dismiss()
        self.music_controller.playlist_add_mopidy((instance.item.item["uri"]))

    def addAndPlayPlaylist(self, instance):
        instance.popup.dismiss()
        song_pos = self.music_controller.get_length_playlist_mopidy()
        self.music_controller.playlist_add_mopidy((instance.item.item["uri"]))
        sleep(1)
        self.music_controller.select_and_play_mopidy(song_pos)

    def onLongpressSearch(self, instance, pos=None):
        # print(instance.item["uri"])
        buttons = [["Add", self.addAlbum], ["Add and Play", self.addAndPlayAlbum], ["Similar", self.similar]]
        musicservers.contextMenu(buttons, instance, colors)

    def similar(self, instance):
        instance.popup.dismiss()
        self.popupSearch.popup.dismiss()
        # print(self.currentArtist)
        self.displaySimilarArtists(self.currentArtist)

    def displaySimilarArtists(self, artist):
        self.similarartists = self.music_controller.do_mopidy_similar(artist)
        # print(self.similarartists)
        self.similarArtistsPopup.display_tracks(artist)

    def addAlbum(self, instance):
        instance.popup.dismiss()
        self.music_controller.playlist_add_mopidy((instance.item.item["album"]["uri"]))

    def addAndPlayAlbum(self, instance):
        # print(instance.item["uri"])
        instance.popup.dismiss()
        song_pos = self.music_controller.get_length_playlist_mopidy()
        print("instance:", instance.item)
        self.music_controller.playlist_add_mopidy((instance.item.item["album"]["uri"]))
        sleep(1)
        self.music_controller.select_and_play_mopidy(song_pos)

    def onSelectTrackAction(self, instance, start):
        # print("play"+instance.id)
        # print ("item:",instance.item)
        self.music_controller.play(start)



        # self.similarArtistsPopup=PopList(maxtracks, self.getsimilarArtistsPopup,self.onSelectsimilarArtistsPopup, self.processsimilarArtistsPopup, self.onLongpresssimilarArtistsPopup)

    def getsimilarArtistsPopup(self):
        return self.similarartists["artists"]

    def processsimilarArtistsPopup(self, item):
        return item["name"]

    def onSelectsimilarArtistsPopup(self, instance, start):
        # self.popupSearch.popup.dismiss()
        temp = self.similarartists["artists"][start]["name"]
        self.popupSearch.artist = temp
        self.popupSearch.display_tracks(temp)

    def onLongpresssimilarArtistsPopup(self, instance, pos):
        pass

    def similarForPlayingArtist(self, instance=None):
        temp1 = self.music_controller.do_mopidy_search(self.currentPlayingArtist)
        self.currentArtist = temp1[0]['tracks'][0]['artists'][0]['uri'].replace("spotify:artist:", "")
        self.displaySimilarArtists(self.currentArtist)
        # following necessary for popupSearch

    def getSearch(self):
        temp1 = self.music_controller.do_mopidy_search(self.popupSearch.artist)
        self.currentArtist = temp1[0]['tracks'][0]['artists'][0]['uri'].replace("spotify:artist:", "")
        print(self.currentArtist)
        temp = temp1[0]["tracks"]
        out_list = []
        added = set()
        for item in temp:
            val = item["album"]["name"]
            if not val in added:
                out_list.append(item)
                added.add(val)
        return out_list

    def mpd_spotify(self, instance):
        self.music_controller.switch()

    def processSearch(self, item):
        # item an be changed if it is an object
        return item["album"]["name"]

    def onSelectSearchAction(self, instance, start):
        self.music_controller.playlist_add_mopidy((instance.item["album"]["uri"]))

    def mode_title(self, instance):
        self.mode_title = not self.mode_title

    def update(self, dt):
        # print("st1:"+self.music_controller.nl)
        try:
            status = self.arduino.exchange()#self.music_controller.get_state()

            # print("st:"+status)
            m, s = divmod(status["elapsed"], 60)
            self.time.text = '{f:02d}:{s:02d}'.format(f=m, s=s)
            m, s = divmod(status["totaltime"], 60)  # track
            self.totaltime.text = '{f:02d}:{s:02d}'.format(f=m, s=s)
            self.tracknr.text = '{f:02d}'.format(f=status["track"])
            self.currentPlayingArtist = status["artist"]
            if self.mode_title:
                self.label.text = "[b]" + self.currentPlayingArtist + " - " + status["title"] + "[/b]"
            else:
                self.label.text = "[b]" + status["album"] + " - " + status["title"] + "[/b]"
            img = status["file"]
            if status['mode'] == 'mpd':
                img = os.path.dirname(img) + "/folder.jpg"
                img = ("http://192.168.2.8:8081/FamilyMusic/" + img).replace(" ", "%20")
                self.get_image(img)
                self.previousimage = img
            else:
                if self.previousimage != img:
                    try:
                        url = "https://api.spotify.com/v1/albums/" + (img.rsplit(':', 2)[2])
                        response = requests.get(url)
                        url = (response.json()["images"][0]["url"])
                        self.get_image(url)
                        self.previousimage = img
                    except:
                        pass


        except:  # catch *all* exceptions
            e = sys.exc_info()[0]
            print(e)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print repr(traceback.extract_tb(exc_traceback))
            self.time.text = '00:00'

    def get_image(self, img):
        if self.image_source != img:
            self.image_source.source = img

    def quit(self):
        App.get_running_app().stop()

    def list_files(self, instance):
        self.selAlbum.popupOpen = False
        self.selAlbum.display("/")
        # print(self.music_controller.mc.list_files("/"))

    def list_smb_files(self, instance):
        self.selSmbAlbum.popupOpen = False
        self.selSmbAlbum.display("/")
        # print(self.music_controller.mc.list_files("/"))
    def doAction(self, instance):
        # print ("action:")
        # print(instance.id)
        self.music_controller.do_action(int(instance.id) - 1)


class MyApp(App):
    def build(self):
        return LoginScreen()


if __name__ == '__main__':
    Config.set("kivy", "keyboard_mode", 'systemanddock')
    Config.write()

    MyApp().run()
