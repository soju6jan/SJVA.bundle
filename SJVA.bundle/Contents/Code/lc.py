# -*- coding: utf-8 -*-
import os
import io
import time
import traceback
from datetime import datetime  
from datetime import timedelta

import base
from lxml import etree

# 선 배포용으로 최근만..
class LiveChannels(object):
    @classmethod
    def get_xml(cls, host, token, section_id, start_channel):
        if section_id == '0': section_id = None
        if section_id is None or section_id == '':
            return cls.make_recentAdd(host, token, start_channel)
        else:
            return cls.make_recentAdd_from_section(host, token, section_id, start_channel)
    
    @classmethod
    def get_xml_one(cls, host, token, section_id, start_channel, count):
        try:
            count = int(count)
        except:
            count = 1000
        return cls.make_recentAdd_one_channel_from_section(host, token, section_id, start_channel, count)
            

        #return 'aaa'

    # 채널당 하나의 에피소드
    # 채널당 여러 방송의 에피소드
    # 채널당 하나의 방송    
    @classmethod
    def make_recentAdd(cls, host, token, start_channel):
        # 채널당 하나의 파일
        try:
            root = etree.Element('tv')
            make_type = 'ONE_FILE_PER_CHANNEL'
            key = '/library/recentlyAdded'
            data = JSON.ObjectFromURL('http://127.0.0.1:32400' + key)
            host = 'http://%s' % host
            token = '?X-Plex-Token=%s' % token
            #Log(data)
            channel_step = 1
            channel_index = 1
            if start_channel is None or start_channel == '': 
                start_channel = 1
            channel_number = int(start_channel)
            if channel_number < 0:
                channel_number = channel_number * -1
                channel_step = -1
            for metadata in data['MediaContainer']['Metadata']:
                if metadata['type'] == 'season':
                    xml_channel = etree.Element('channel')
                    #xml_channel.attrib['id'] = metadata['key']
                    xml_channel.attrib['id'] = u'%s' % channel_number
                    xml_channel.attrib['repeat-programs'] = 'true'
                    xml_channel_name = etree.Element('display-name')
                    #xml_channel_name.text = metadata['parentTitle']
                    xml_channel_name.text = u'최신(%s)' % channel_index
                    xml_channel_number = etree.Element('display-number')
                    xml_channel_number.text = str(channel_number)
                    #xml_channel_icon = etree.Element('icon')
                    #xml_channel_icon.attrib['src'] = '%s%s%s' % (host, metadata['thumb'], token)
                    
                    xml_channel.append(xml_channel_name)
                    xml_channel.append(xml_channel_number) 
                    #xml_channel.append(xml_channel_icon)  

                    episodes_url = '%s%s%s' % (host, metadata['key'], token)
                    sub_data = JSON.ObjectFromURL(episodes_url)
                    #Log(sub_data)
                    episode = sub_data['MediaContainer']['Metadata'][0]
                    xml_programme = etree.Element('programme')
                    part = episode['Media'][0]['Part'][0]
                    if 'duration' not in part: # 분석 전..
                        continue
                    datetime_start = datetime(2019,1,1) + timedelta(hours=-9)
                    datetime_stop = datetime_start + timedelta(seconds=int(part['duration'])/1000+1)
                    xml_programme.attrib['start'] = '%s +0900' % datetime_start.strftime('%Y%m%d%H%M%S') 
                    xml_programme.attrib['stop'] = '%s +0900' % datetime_stop.strftime('%Y%m%d%H%M%S') 
                    xml_programme.attrib['channel'] = u'%s' % channel_number
                    xml_programme.attrib['video-src'] = '%s%s%s' % (host, part['key'], token)
                    xml_programme.attrib['video-type'] = 'HTTP_PROGRESSIVE'
                    xml_programme_title = etree.Element('title')
                    if 'index' in episode:
                        xml_programme_title.text = '%s회 %s %s' % (episode['index'], metadata['parentTitle'], episode['title'].strip())
                    else:
                        xml_programme_title.text = '%s %s' % (metadata['parentTitle'], episode['title'].strip())
                    xml_programme_desc = etree.Element('desc')
                    xml_programme_desc.text = episode['summary'].strip()
                    xml_programme_icon = etree.Element('icon')
                    xml_programme_icon.attrib['src'] = '%s%s%s' % (host, episode['thumb'], token)
                    xml_programme_category = etree.Element('category')
                    xml_programme_category.text = u'최신'
                    xml_programme.append(xml_programme_title)
                    xml_programme.append(xml_programme_desc)
                    xml_programme.append(xml_programme_icon)
                    xml_programme.append(xml_programme_category)
                    root.append(xml_channel)
                    root.append(xml_programme) 
                    channel_number += channel_step
                    channel_index += 1
            output = etree.tostring(root, pretty_print=True, encoding='UTF-8')
            #Log(x_output)
            header = '<?xml version="1.0" encoding="UTF-8"?>\n'        
            header += '<!DOCTYPE tv SYSTEM "xmltv.dtd">\n'
            xml = header + output
            return xml.replace('&#13;', '')
        except Exception as e:
            Log('Exception : %s', e)
            Log(traceback.format_exc()) 
        finally:
            pass
   
    @classmethod
    def make_recentAdd_from_section(cls, host, token, section_id, start_channel):
        # 채널당 하나의 파일
        try:
            section_title = base.get_section_title_from_id(section_id)
            root = etree.Element('tv')
            make_type = 'ONE_FILE_PER_CHANNEL'
            key = '/library/sections/%s/recentlyAdded' % section_id
            data = JSON.ObjectFromURL('http://127.0.0.1:32400' + key)
            host = 'http://%s' % host
            token = '?X-Plex-Token=%s' % token
            #Log(data) 
            channel_step = 1
            channel_index = 1            
            if start_channel is None or start_channel == '': 
                start_channel = 1
            channel_number = int(start_channel)
            if channel_number < 0:
                channel_number = channel_number * -1
                channel_step = -1
            if data['MediaContainer']['viewGroup'] == 'episode':
                for metadata in data['MediaContainer']['Metadata']:
                    #if metadata['type'] == 'season':
                        xml_channel = etree.Element('channel')
                        #xml_channel.attrib['id'] = metadata['ratingKey']
                        xml_channel.attrib['id'] = u'%s' % channel_number
                        xml_channel.attrib['repeat-programs'] = 'true'
                        xml_channel_name = etree.Element('display-name')
                        #xml_channel_name.text = metadata['grandparentTitle']
                        xml_channel_name.text = u'%s(%s)' % (section_title, channel_index)
                        xml_channel_number = etree.Element('display-number')
                        xml_channel_number.text = str(channel_number)
                        #xml_channel_icon = etree.Element('icon')
                        #xml_channel_icon.attrib['src'] = '%s%s%s' % (host, metadata['thumb'], token)
                        xml_channel.append(xml_channel_name)
                        xml_channel.append(xml_channel_number) 
                        #xml_channel.append(xml_channel_icon)  

                        # = metadata['Media'][0]
                        xml_programme = etree.Element('programme')
                        part = metadata['Media'][0]['Part'][0]
                        if 'duration' not in part: # 분석 전..
                            continue
                        datetime_start = datetime(2019,1,1) + timedelta(hours=-9)
                        datetime_stop = datetime_start + timedelta(seconds=int(part['duration'])/1000+1)
                        xml_programme.attrib['start'] = '%s +0900' % datetime_start.strftime('%Y%m%d%H%M%S') 
                        xml_programme.attrib['stop'] = '%s +0900' % datetime_stop.strftime('%Y%m%d%H%M%S') 
                        xml_programme.attrib['channel'] = u'%s' % channel_number
                        xml_programme.attrib['video-src'] = '%s%s%s' % (host, part['key'], token)
                        xml_programme.attrib['video-type'] = 'HTTP_PROGRESSIVE'
                        xml_programme_title = etree.Element('title')
                        if 'index' in metadata:
                            xml_programme_title.text = '%s회 %s %s' % (metadata['index'], metadata['grandparentTitle'], metadata['title'].strip())
                        else:
                            xml_programme_title.text = '%s %s' % (metadata['grandparentTitle'], metadata['title'].strip())
                        xml_programme_desc = etree.Element('desc')
                        xml_programme_desc.text = metadata['summary'].strip()
                        xml_programme_icon = etree.Element('icon')
                        xml_programme_icon.attrib['src'] = '%s%s%s' % (host, metadata['thumb'], token)
                        xml_programme_category = etree.Element('category')
                        xml_programme_category.text = section_title
                        xml_programme.append(xml_programme_title)
                        xml_programme.append(xml_programme_desc)
                        xml_programme.append(xml_programme_icon)
                        xml_programme.append(xml_programme_category)
                        root.append(xml_channel)
                        root.append(xml_programme)
                        channel_number += channel_step
                        channel_index += 1
            elif data['MediaContainer']['viewGroup'] == 'movie':
                for metadata in data['MediaContainer']['Metadata']:
                    #if metadata['type'] == 'season':
                        #Log(metadata)
                        try:
                            if metadata['Media'][0]['audioCodec'] not in ['aac', 'mp3']: continue
                        except:
                            pass
                        xml_channel = etree.Element('channel')
                        xml_channel.attrib['id'] = u'%s' % channel_number
                        xml_channel.attrib['repeat-programs'] = 'true'
                        xml_channel_name = etree.Element('display-name')
                        #xml_channel_name.text = metadata['title']
                        xml_channel_name.text = u'%s(%s)' % (section_title, channel_index)
                        xml_channel_number = etree.Element('display-number')
                        xml_channel_number.text = str(channel_number)
                        #xml_channel_icon = etree.Element('icon')
                        #xml_channel_icon.attrib['src'] = '%s%s%s' % (host, metadata['thumb'], token)
                        xml_channel.append(xml_channel_name)
                        xml_channel.append(xml_channel_number) 
                        #xml_channel.append(xml_channel_icon)   

                        # = metadata['Media'][0]
                        xml_programme = etree.Element('programme')
                        part = metadata['Media'][0]['Part'][0]
                        if 'duration' not in part: # 분석 전..
                            continue
                        datetime_start = datetime(2019,1,1) + timedelta(hours=-9)
                        datetime_stop = datetime_start + timedelta(seconds=int(part['duration'])/1000+1)
                        xml_programme.attrib['start'] = '%s +0900' % datetime_start.strftime('%Y%m%d%H%M%S') 
                        xml_programme.attrib['stop'] = '%s +0900' % datetime_stop.strftime('%Y%m%d%H%M%S') 
                        xml_programme.attrib['channel'] = u'%s' % channel_number
                        xml_programme.attrib['video-src'] = '%s%s%s' % (host, part['key'], token)
                        xml_programme.attrib['video-type'] = 'HTTP_PROGRESSIVE'
                        xml_programme_title = etree.Element('title')
                        xml_programme_title.text = metadata['title'].strip()
                        xml_programme_desc = etree.Element('desc')
                        xml_programme_desc.text = metadata['summary'].strip()
                        xml_programme_icon = etree.Element('icon')
                        xml_programme_icon.attrib['src'] = '%s%s%s' % (host, metadata['thumb'], token)
                        xml_programme_category = etree.Element('category')
                        xml_programme_category.text = section_title
                        xml_programme.append(xml_programme_title)
                        xml_programme.append(xml_programme_desc)
                        xml_programme.append(xml_programme_icon)
                        xml_programme.append(xml_programme_category)
                        root.append(xml_channel)
                        root.append(xml_programme)
                        channel_number += channel_step
                        channel_index += 1
            output = etree.tostring(root, pretty_print=True, encoding='UTF-8')
            #Log(x_output)
            header = '<?xml version="1.0" encoding="UTF-8"?>\n'        
            header += '<!DOCTYPE tv SYSTEM "xmltv.dtd">\n'
            xml = header + output
            return xml.replace('&#13;', '')
        except Exception as e:
            Log('Exception : %s', e)
            Log(traceback.format_exc()) 
        finally:
            pass

    @classmethod
    def make_recentAdd_one_channel_from_section(cls, host, token, section_id, channel_no, count):
        try:
            section_title = base.get_section_title_from_id(section_id)
            root = etree.Element('tv')
            key = '/library/sections/%s/recentlyAdded' % section_id
            data = JSON.ObjectFromURL('http://127.0.0.1:32400' + key)
            host = 'http://%s' % host
            token = '?X-Plex-Token=%s' % token
            #Log(data) 
            xml_channel = etree.Element('channel')
            xml_channel.attrib['id'] = channel_no
            xml_channel.attrib['repeat-programs'] = 'true'
            xml_channel_name = etree.Element('display-name')
            xml_channel_name.text = section_title
            xml_channel_number = etree.Element('display-number')
            xml_channel_number.text = channel_no
            xml_channel.append(xml_channel_name)
            xml_channel.append(xml_channel_number) 
            root.append(xml_channel)
            datetime_start = datetime(2019,1,1) + timedelta(hours=-9)
            programm_count = 0
            for metadata in data['MediaContainer']['Metadata']:
                try:
                    if metadata['Media'][0]['audioCodec'] not in ['aac', 'mp3']: continue
                except:
                    continue
                try:
                    xml_programme = etree.Element('programme')
                    part = metadata['Media'][0]['Part'][0]
                    if 'duration' not in part: # 분석 전..
                        continue
                    datetime_stop = datetime_start + timedelta(seconds=int(part['duration'])/1000+1)
                    xml_programme.attrib['start'] = '%s +0900' % datetime_start.strftime('%Y%m%d%H%M%S') 
                    xml_programme.attrib['stop'] = '%s +0900' % datetime_stop.strftime('%Y%m%d%H%M%S') 
                    xml_programme.attrib['channel'] = channel_no
                    xml_programme.attrib['video-src'] = '%s%s%s' % (host, part['key'], token)
                    xml_programme.attrib['video-type'] = 'HTTP_PROGRESSIVE'
                    xml_programme_title = etree.Element('title')
                    xml_programme_title.text = metadata['title'].strip()
                    xml_programme_desc = etree.Element('desc')
                    xml_programme_desc.text = metadata['summary'].strip()
                    xml_programme_icon = etree.Element('icon')
                    xml_programme_icon.attrib['src'] = '%s%s%s' % (host, metadata['thumb'], token)
                    xml_programme_category = etree.Element('category')
                    xml_programme_category.text = section_title
                    xml_programme.append(xml_programme_title)
                    xml_programme.append(xml_programme_desc)
                    xml_programme.append(xml_programme_icon)
                    xml_programme.append(xml_programme_category)
                    datetime_start = datetime_stop
                    root.append(xml_programme)
                    programm_count += 1
                    if programm_count >= count:
                        break
                except Exception as e:
                    Log('Exception : %s', e)
                    Log(traceback.format_exc()) 
            output = etree.tostring(root, pretty_print=True, encoding='UTF-8')
            header = '<?xml version="1.0" encoding="UTF-8"?>\n'        
            header += '<!DOCTYPE tv SYSTEM "xmltv.dtd">\n'
            xml = header + output
            return xml.replace('&#13;', '')
        except Exception as e:
            Log('Exception : %s', e)
            Log(traceback.format_exc()) 
        finally:
            pass


    """
    @classmethod
    def get_tvh_m3u(cls, host, token):
        try:
            ret = '#EXTM3U\n' 
            ret += '#EXTINF:-1,PLEX\n'
            #ret += 'http://%s/:/plugins/com.plexapp.plugins.SJVA/function/tvhfile?X-Plex-Token=%s' % (host, token)
            ret += 'tcp://192.168.0.11:34501'
            return ret
            #ret += 'pipe:///usr/bin/ffmpeg -loglevel fatal -i http://%s/:/plugins/com.plexapp.plugins.SJVA/function/tvhfile?X-Plex-Token=%s -codec copy -acodec copy -metadata service_provider=PLEX -metadata service_name=PLEX -tune zerolatency -f mpegts pipe:1' % (host, token)
            file = cls.get_tvh_file(host, token)
            ret += 'pipe:///usr/bin/ffmpeg -loglevel fatal -i %s -codec copy -acodec copy -metadata service_provider=PLEX -metadata service_name=PLEX -tune zerolatency -f mpegts pipe:1' % (file)
            return ret
        except Exception as e:
            Log('Exception : %s', e)
            Log(traceback.format_exc()) 
        finally: 
            pass

    @classmethod
    def get_tvh_file(cls, host, token):
        try:
            key = '/playlists'
            data = JSON.ObjectFromURL('http://127.0.0.1:32400' + key)
            host = 'http://%s' % host
            token = '?X-Plex-Token=%s' % token
            Log(data)
            key = None
            ret = 'concat:'
            for metadata in data['MediaContainer']['Metadata']:
                if metadata['title'] == 'tvh':
                    key = metadata['key']
                    break
            if key is not None:
                data = JSON.ObjectFromURL('http://127.0.0.1:32400' + key)
                Log(data)
                for metadata in data['MediaContainer']['Metadata']:
                    part = metadata['Media'][0]['Part'][0]
                    #return part['key']
                    #ret += '%s%s%s' % (host, part['key'], token) + '|'
                    file = '%s%s%s' % (host, part['key'], token)
                    ret = 'pipe:///usr/bin/ffmpeg -loglevel fatal -i %s -codec copy -acodec copy -metadata service_provider=PLEX -metadata service_name=PLEX -tune zerolatency -f mpegts pipe:1' % (file)
                    return ret
            return '"%s"' % ret[:-1]
        except Exception as e:
            Log('Exception : %s', e)
            Log(traceback.format_exc()) 
        finally:
            pass
    """
    
