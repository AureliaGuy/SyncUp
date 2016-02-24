
import spotify
import threading
from pythonPandora import PandoraClient
from pythonPandora import spotify_session
import os

"""Class adds songs to Spotify playlists from Pandora"""
class addSongs(object):
    url_to_login = "https://www.spotify.com/login"
    stationDict = {}
    stationsSet = set()
    stationCount = 0
    listmp4s = []
    iTunesSongs = set()

    def __init__(self):
        self.session = spotify_session().session
        self.name_of_tracks = {}

    """Initialization of playlists and songs. Run once when first creating playlists"""
    def add_playlists(self):
        pythonStart = PandoraClient("__insert_Pandora_username__", "__insert_Pandora_password__")
        pythonStart.liked_tracks()

        for station in pythonStart.station_dictionary:
            for playlist in self.session.playlist_container:
                playlist.load()
                if station in playlist.name:
                    curr_playlist = playlist 
                    break
            else:
                curr_playlist = self.session.playlist_container.add_new_playlist(station)
            for song in pythonStart.station_dictionary[station]:
                for s in curr_playlist.tracks:
                    s.load()
                    if song in s.name:
                        break
                else: 
                    try:
                        self.session.process_events()
                        search = self.session.search(song)
                        search.loaded_event.wait()
                        track = search.tracks[0]
                        curr_playlist.add_tracks(track)
                        self.session.process_events()
                        self.name_of_tracks[station] = [track.name]
                    except IndexError:
                        print song

    """Updates the playlists, adding songs that the user has recently liked and deleting songs that the 
    user no longer likes"""
    def update_playlists(self):
        pythonStart = PandoraClient("__insert_Pandora_username__", "__insert_Pandora_password__")
        pythonStart.liked_tracks()

        container = self.session.playlist_container
        container.load()

        for playlist in container:
            playlist.load()
            for j in pythonStart.station_dictionary:
                if (j in playlist.name):
                    count = 0
                    for track in playlist.tracks:
                        track.load()
                        if (track.name not in pythonStart.station_dictionary[j]):
                            playlist.remove_tracks(count)
                            self.session.process_events()
                        count += 1
        self.add_playlists()

    """Retrieves iTunes song titles from the user's computer"""
    def retrieve_iTunes(self, filename):
        directory = os.path.dirname(filename)
        subDirectories = [x for x in os.listdir(directory)]
        for i in subDirectories:
            if ("m4a" in i):
                start_index = 0
                while (i[start_index] != " "):
                    start_index += 1
                end_index = i.find("m4a")
                song_name = i[start_index + 1: end_index -1]
                addSongs.iTunesSongs.add(song_name)
                break
            else:
                self.retrieve_iTunes(filename + i + "/")
                
    """Creates spotify playlist of all downloaded songs from iTunes"""
    def add_iTunes(self):
        trackList = []
        if "iTunes_playlist" not in addSongs.stationsSet:
            playlist = self.session.playlist_container.add_new_playlist("iTunes_playlist")
            addSongs.stationsSet.add("iTunes_playlist")
            addSongs.stationDict["iTunes_playlist"] = len(self.session.playlist_container) -1
        else:
            playlist = self.session.playlist_container[addSongs.stationDict["iTunes_playlist"]]
        self.session.process_events()
        for song_name in addSongs.iTunesSongs:
            search = self.session.search(song_name)
            search.loaded_event.wait()
            track = search.tracks[0]
            trackList.append(track)
        playlist.add_tracks(trackList)
        playlist.set_offline_mode()
        self.session.process_events()

def main():
    p = addSongs()
    #p.add_playlists()
    p.update_playlists()
    #p.retrieve_iTunes("/home/__insert_name__/Music/iTunes/iTunes Media/Music/");
    #p.add_iTunes()
    #print p.session.playlist_container[addSongs.stationDict["iTunes_playlist"]].tracks
    p.session.process_events()
    #p.add_playlists()

main()
