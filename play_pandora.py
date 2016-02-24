import requests
import lxml.html
import re 
import datetime
from urllib2 import Request, build_opener, HTTPCookieProcessor, HTTPHandler
import cookielib
import webbrowser
import os
import Cookie
import cgi
import threading
import spotify
from libmproxy.proxy.server import ProxyServer
from libmproxy import controller, proxy
import os, sys, re, datetime, json
from random import randint
from selenium import webdriver
from selenium.webdriver.common.proxy import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support import ui
from selenium.webdriver.common.keys import Keys
from multiprocessing import Process
import multiprocessing as mp
import time

"""Tests for correct station being played on Spotify""""
station = "Today's Hits Radio"
station_dict = {'2723668143942053214': "Shuffle", "2723668139647085918": "Today's Hits Radio"}
global driver

class PandoraClient(object):
    URL_TO_LOGIN = "https://www.pandora.com/login"
    
    """"Initialize PandoraClient class to retrieve liked songs from Pandora"""
    def __init__(self, user, password):
        self.session = requests.session()
        self.USERNAME = "__insert_Pandora_username__"
        self.artists = []
        self.songs = []
        self.stations = []
        self.station_dictionary = {}
        response = self.session.post(PandoraClient.URL_TO_LOGIN, data = {"login_username": user,"login_password": password,})
   
    """Test method"""   
    def ad_check(self):
        PANDORA_URL ="http://www.pandora.com"
        count = 0
        while count < 100000: 
            count += 1
            full = requests.get(PANDORA_URL)
            x = full.cookies.items()
            for i, j in x:
                print i +  " " + j
    
    """Retrieve liked songs, artists and stations from pandora""""
    def liked_tracks(self):
        like_start_index = 0
        thumb_start_index = 0
        while (True):
            LIKES_URL = "http://www.pandora.com/content/tracklikes?likeStartIndex=5&thumbStartIndex=" + str(thumb_start_index) + "&webname=" + self.USERNAME
            notFinished = False
            none = False
            start = ""
            noPrint = False
            count = 0
            full = self.session.get(LIKES_URL, params = {"likeStartIndex": like_start_index,"thumbStartIndex": thumb_start_index,})
            s = ""
            for child in full:
                count += 1
                s += child
                
            """If there are no more songs to add, breaks out of loop"""
            if (count == 1):
                break
            
            """The index of the song and artist will correspond to the index of its stationname"""
            for x in re.finditer('class="like_context_stationname">', s):
                index_start = x.start() + 33
                index_end = index_start
                while(s[index_end] != "<"):
                    index_end += 1
                id_number = x.start()
                while (s[id_number] != "="):
                    id_number -= 1
                self.stations.append(s[index_start: index_end])
                
            """The artist's index in list will correspond to the index of the song and stationname"""
            for j in re.finditer('by <a href="/', s):
                index_start = j.start() + 14
                while (s[index_start] != ">"):
                    index_start += 1
                index_start += 1
                index_end = index_start
                while (s[index_end] != "<"):
                    index_end += 1
                self.artists.append(s[index_start: index_end])
                
            """Retrieve song name and append it to list of songs"""
            for i in re.finditer('class="first"',s):
                index_start = i.start() + 14
                index_end = index_start
                while (s[index_end] != "<" and s[index_end] != "("):
                    index_end += 1
                self.songs.append(s[index_start: index_end])
            thumb_start_index += 10
        count = 0;
        
        """If already created station playlist, append song to the list of songs for that station. Otherwise, 
        create a new dictionary list entry for that station"""
        while (count < len(self.stations)):
            if (self.stations[count] in self.station_dictionary):
                self.station_dictionary[self.stations[count]].append(self.songs[count])
            else:
                self.station_dictionary[self.stations[count]] = [self.songs[count]]
            count += 1
            
    """Method initializes and runs mitm proxy"""
    def call_proxy(self, q):
        config = proxy.ProxyConfig(port=8080)
        server = proxy.server.ProxyServer(config)
        m = StickyMaster(server, q)
        m.run()

    """Open pandora with multithreading, so that we can listen to Pandora while monitoring http feed"""
    def open_pandora(self):
        q = mp.Queue()
        mitm_proxy = Process(target=self.call_proxy, args=(q,))
        mitm_proxy.start()
        play_session = play_spotify(station)
        
        """Use webdriver to open and login to user's Pandora account"""
        while (True):    
            initial_size = q.qsize()
            PROXY_PORT = "8080"
            PROXY_HOST ="127.0.0.1"

            profile = webdriver.FirefoxProfile()
            profile.accept_untrusted_certs = True
            profile.set_preference("network.proxy.type", 1)

            profile.set_preference("network.proxy.http",PROXY_HOST)
            profile.set_preference("network.proxy.http_port",int(PROXY_PORT))
            profile.update_preferences()

            driver =  webdriver.Firefox(firefox_profile=profile)
            
            driver.set_window_size(3000, 5000)
            driver.set_window_position(200, 200)

            """Web scraping of pertinent information for webdriver to login to Pandora""" 
            username = "__insert_Pandora_username__"
            password = "__insert_Pandora_password__"
            driver.get("http://www.pandora.com")
            driver.find_element(By.CSS_SELECTOR, "div.message:nth-child(1) > a:nth-child(1)").click()
            driver.find_element(By.CSS_SELECTOR, "div.formField:nth-child(1) > input:nth-child(1)").send_keys(username)
            driver.find_element(By.CSS_SELECTOR, "div.formField:nth-child(2) > input:nth-child(1)").send_keys(password)
            driver.find_element(By.CSS_SELECTOR, "input.btn_bg").click()    

            """Continue until a command to switch to spotify is appended to q in parallel process"""
            while (initial_size == q.qsize()):
                continue
                
            """Quit driver once command appended to q"""
            driver.quit()
            
            """Open Spotify webbrowser and play Spotify"""
            webbrowser.get("/usr/bin/google-chrome").open_new("https://play.spotify.com/user/lia-777/playlist/1wypu7dCiXSvH40RKhiiIS")
            play_session.play()
           

"""Uses Spotify API to play song from selected Pandora playlist until switch back to Pandora after advertisement"""
class play_spotify(object):
    def __init__(self, station):
        self.session = spotify.Session()
        self.station = station
        audio = spotify.AlsaSink(self.session)
        loop = spotify.EventLoop(self.session)
        loop.start()
        self.session.login("__insert_Spotify_username__", "__insert_Spotify_password__")
        while self.session.connection.state != spotify.ConnectionState.LOGGED_IN:
            self.session.process_events()
            
    """Play a random song from selected playlist"""
    def play(self):    
        for playlist in self.session.playlist_container.load():
            print playlist.load().name
            if playlist.load().name == self.station:
                tracks = playlist.load().tracks
                index = randint(0, len(tracks) -1)
                track = tracks[index].load()
                self.session.player.load(track)
                self.session.player.play()
                try:
                    time.sleep(track.duration/1000);
                except KeyboardInterrupt:
                    pass
                break
               

class spotify_session(object):
    
    """Initialize Spotify session"""
    def __init__(self):
        logged_in_event = threading.Event()
        def connection_state_listener(session):
            if session.connection.state is spotify.ConnectionState.LOGGED_IN:
                logged_in_event.set()
        self.session = spotify.Session()
        audio = spotify.AlsaSink(self.session)
        loop = spotify.EventLoop(self.session)
        loop.start()
        self.session.on(
            spotify.SessionEvent.CONNECTION_STATE_UPDATED,
            connection_state_listener)
        self.session.login("__insert_Spotify_username__", "__insert_Spotify_password__")
        logged_in_event.wait()

"""Class for man-in-the-middle proxy that monitors http traffic from Pandora"""
class StickyMaster(controller.Master):

    def __init__(self, server, q):
        self.q = q
        controller.Master.__init__(self, server)
        self.stickyhosts = {}

    def run(self):
        try:
            return controller.Master.run(self)
        except KeyboardInterrupt:
            self.shutdown()
    
    """Pandora sends how many skips user has remaining in http traffic to and from site"""      
    def out_of_skips(self, flow_str):
        return ("out_of_station_skips=true" in flow_str)
    
    """Switches to spotify if reach skip limit or advertisement- information request from Pandora"""
    def handle_request(self, flow):
        if self.is_ad(str(flow.request)) or self.out_of_skips(str(flow.request)):
            self.q.put("switch to spotify")
        flow.reply()
   

    """Pandora sends identifiable GET http requests when an advertisement replaces the music"""
    def is_ad(self, flow_str):
        strRedirect = "http://www.pandora.com:80/util/mediaserverPublicRedirect." 
        strAudio = "audio"
        strVid = "http://video.moatads.com"
        strVideo = "http://player.ooyala.com:80/nuplayer?autoplay=1"
        strVideo2 = "http://l.ooyala.com:80/verify?" 
        if strRedirect in flow_str and strAudio in flow_str:
           return True
        elif strVideo in flow_str or strVideo2 in flow_str:
           return True
        else:
            return False
    
    """Proxy checks to see if Pandora is playing advertisement or has reached skip limit. 
    If so, it puts a command to switch to spotify in the pipe. Information response to Pandora"""
    def handle_response(self, flow):
        if self.is_ad(str(flow.request)) or self.out_of_skips(str(flow.request)):
            self.q.put("switch to spotify")
        flow.reply()

"""Find the URI of the pandora station playlist you are currently on and open that playlist in spotify"""
def main(argv):
    p = PandoraClient("__insert_Pandora_username__", "__insert_Pandora_password__")
    p.open_pandora()

"""Main function"""
if __name__ == '__main__':
  main(sys.argv)
