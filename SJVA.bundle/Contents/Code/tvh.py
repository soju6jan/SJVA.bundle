# -*- coding: utf-8 -*-
import os
import io
import time
import traceback

sample_key_list = [
    '/library/recentlyAdded',
    '/playlists/tvh'
]

class TVHeadend(object):
    streaming_list = None

    @classmethod
    def tvhm3u(cls, host, token):
        m3u = '#EXTM3U\n' 
        for index, value in enumerate(sample_key_list):
            m3u += '#EXTINF:-1,PLEX %s-1\n' % (index+1)
            m3u += 'pipe:///usr/bin/ffmpeg -loglevel fatal -i http://%s/:/plugins/com.plexapp.plugins.SJVA/function/tvhurl?key=%s&streaming_type=m3u8&X-Plex-Token=%s -codec copy -acodec copy -metadata service_provider=PLEX -metadata service_name=PLEX -tune zerolatency -f mpegts pipe:1\n' % (host, value, token)
            m3u += '#EXTINF:-1,PLEX %s-2\n' % (index+1)
            m3u += 'pipe:///usr/bin/ffmpeg -loglevel fatal -i http://%s/:/plugins/com.plexapp.plugins.SJVA/function/tvhurl?key=%s&streaming_type=file&X-Plex-Token=%s -codec copy -acodec copy -metadata service_provider=PLEX -metadata service_name=PLEX -tune zerolatency -f mpegts pipe:1\n' % (host, value, token)
        return m3u
        
    @classmethod
    def init_list(cls):
        #if cls.streaming_list is None:
        cls.streaming_list = []
        for key in sample_key_list:
            cls.streaming_list.append(Broadcast(key))
            cls.streaming_list.append(Broadcast(key))
        return len(cls.streaming_list)

    @classmethod
    def tvhurl(cls, key, streaming_type, host, token):
        if cls.streaming_list is None or len(cls.streaming_list) == 0:
            cls.init_list()
        for streaming in cls.streaming_list:
            if streaming.key == key:
                return Redirect(streaming.get_url(streaming_type, host, token))
    
class Broadcast(object):
    def __init__(self, key):
        self.key = key
        self.video_list = []
        self.timestamp = time.time()
        self.total_duration = 0
        self.file_index = 0
        try:
            if key.startswith('/playlists'):
                tmp_key = '/playlists' 
                data = JSON.ObjectFromURL('http://127.0.0.1:32400' + tmp_key)
                for metadata in data['MediaContainer']['Metadata']:
                    if metadata['title'] == key.split('/')[-1]:
                        key = metadata['key']
            data = JSON.ObjectFromURL('http://127.0.0.1:32400' + key)
            #Log(data)
            for metadata in data['MediaContainer']['Metadata']:
                try:
                    sub_data = JSON.ObjectFromURL('http://127.0.0.1:32400' + metadata['key'])
                    #Log(sub_data)
                    episode = sub_data['MediaContainer']['Metadata'][0]
                    #Log(episode)
                    self.video_list.append({'key':episode['key'], 'duration':int(episode['duration']), 'file':episode['Media'][0]['Part'][0]['key']})
                    self.total_duration = self.total_duration + int(episode['duration'])
                    #Log(episode['duration'])
                except:
                    pass 
            #Log(self.video_list)
            Log('TOTAL_DURATION : %s', self.total_duration)
        except Exception as e:
            Log('Exception : %s', e) 
            Log(traceback.format_exc()) 

    def get_url(self, streaming_type, host, token):
        if streaming_type == 'm3u8':
            #duration은 ms   timestamp는 s.. 쿼리는 초
            offset = (time.time() - self.timestamp) * 1000 % self.total_duration
            tmp = 0
            for video in self.video_list:
                Log('offset %s tmp %s duration %s', offset, tmp, video['duration'])
                if offset + 5*1000 < tmp + video['duration']:
                    url = 'http://%s/video/:/transcode/universal/start.m3u8?X-Plex-Platform=Chrome&mediaIndex=0&offset=%s&path=%s&X-Plex-Token=%s' % (host, ((offset-tmp)/1000-1), video['key'], token)
                    Log(url)
                    return url
                else:
                    tmp = tmp + video['duration']
        elif streaming_type == 'file':
            url = 'http://%s%s?X-Plex-Token=%s' % (host, self.video_list[self.file_index % len(self.video_list)]['file'], token)
            #Log(url)
            self.file_index = self.file_index + 1
            return url

        
"""
#멀티 접근??
@classmethod
    def tvhfile(cls, host, token): 
        if cls.video_list is None or len(cls.video_list) == 0:
            cls.init_list(host, token)
        url = None
        if cls.video_list is not None and len(cls.video_list) > 0:
            url = cls.video_list[cls.index % len(cls.video_list)]
            cls.index = cls.index + 1
        Log('tvhfile %s %s' % (cls.index, url))     
        return Redirect(url)
        #return url
"""