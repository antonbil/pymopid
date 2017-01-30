import json

import utils

try:
    import mpd.base as mpd
except:
    import mpd

import requests.api as requests
import difflib

mpdServerUrl = "192.168.2.74"


class mpd_controller:
    def __init__(self):
        self.connect_mpd()

    def connect_mpd(self):
        self.client = mpd.MPDClient()
        try:
            self.client.connect(mpdServerUrl, 6600)
        except mpd.ConnectionError:
            pass

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
        volume = (int(mpd_status['volume']) - 80) / 2
        currentsong = self.get_client().currentsong()
        numbers = currentsong["track"].rsplit('/', 1)
        track = int(numbers[0])  # current track
        try:
            totaltracks = int(numbers[1])  # total tracks
        except:
            totaltracks = 0
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
        if len(uri) > 1:
            uri = utils.remove_slash_at_end(uri)
            uri = utils.remove_slash_at_start(uri)
        result = self.get_client().lsinfo(uri)
        return result

    def add(self, uri):
        return self.get_client().add(uri)

    def remove_track(self, songpos):
        return self.get_client().delete(songpos)

    def list_artists(self):
        return self.get_client().list("artist")
        # $pl->delete( $song [, $song [...] ] );


class music_controller:
    mc = mpd_controller()

    nl = "2"

    def __init__(self):
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

    def browse_mopidy(self, uri):
        res = self.do_param_mopidy_call("core.library.browse", {'uri': uri})
        return res["result"]

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
                try:
                    m, s = divmod(item['length'] / 1000, 60)
                    # track_no
                    t = item["track_no"]
                    text = '{t:02d}-{artist}-{title}({f:02d}:{s:02d})'.format(f=m, s=s, t=t,
                                                                              artist=item["artists"][0]["name"].encode(
                                                                                  'utf-8'),
                                                                              title=item["name"].encode('utf-8'))
                    playlist.append(text)
                except:
                    pass
            return playlist

    def do_mopidy_call(self, mopidyaction):
        data = {"jsonrpc": "2.0", "id": 1, "method": mopidyaction}
        headers = {'content-type': 'application/json'}
        url = 'http://' + mpdServerUrl + ':6680/mopidy/rpc'

        data1 = json.dumps(data)
        return requests.post(url, data=data1, headers=headers).json()["result"]

    def get_mopidy_playlists(self, instance=None):
        result = self.do_mopidy_call("core.playlists.as_list")
        # print(result)
        return result

    def do_mopidy_similar(self, artist):
        url = "https://api.spotify.com/v1/artists/" + artist + "/related-artists"
        res = requests.get(url, verify=False).json()
        return res

    def do_mopidy_search(self, artist):
        data = {"jsonrpc": "2.0", "id": 1, "params": {'query': {'artist': [artist]}}, "exact": "True",
                "method": "core.library.search"}
        headers = {'content-type': 'application/json'}
        url = 'http://' + mpdServerUrl + ':6680/mopidy/rpc'

        data1 = json.dumps(data)
        res = requests.post(url, data=data1, headers=headers).json()
        return res["result"]

    def clear_tracks(self, instance=None):
        if self.engine == "mpd":
            self.mc.clear_tracks()

        else:
            self.do_mopidy_call("core.tracklist.clear")

    def do_action(self, action):
        if action == 4:
            # App.get_running_app().stop()
            return  # menu-button
        if self.engine == "mpd":
            # Get the function from switcher dictionary
            func = self.mpdswitcher.get(action, lambda: "nothing")
            func()
        else:
            # do nothing
            todo = self.mopidyswitcher[action]
            if todo=="previous":
                pos=self.get_mopidy_index()
                if pos==0:
                    pos = self.get_length_playlist_mopidy()
                pos=pos-1
                self.select_and_play_mopidy(pos)
            else:
                if todo=="next":
                    pos=self.get_mopidy_index()
                    pos2 = self.get_length_playlist_mopidy()-1
                    if pos==pos2:
                        self.select_and_play_mopidy(0)
                        return

                response = self.do_mopidy_call("core.playback." + todo)
        return

    def get_mopidy_playlist(self):
        return self.do_mopidy_call("core.tracklist.get_tracks")

    def get_mopidy_index(self):
        return self.do_mopidy_call("core.tracklist.index")
    
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
        # print (res)
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
