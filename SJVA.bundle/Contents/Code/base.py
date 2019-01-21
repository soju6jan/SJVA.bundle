# -*- coding: utf-8 -*-
import os
import re
import traceback
import subprocess
import sys
import threading

sys.setdefaultencoding('utf-8')

VERSION = '2019-01-20 04' 
OS = Platform.OS
CURRENT_PATH = re.sub(r'^\\\\\?\\', '', os.getcwd())
DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_PATH))), 'Plug-in Support', 'Databases', 'com.plexapp.plugins.library.db')
#SQLITE3 = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_PATH))), 'Plug-ins', 'SJVA.bundle', 'pms', OS, 'sqlite3') 

PYTHON = 'python'       
if OS == 'Windows':
    SCANNER = r'C:\\Program Files (x86)\\Plex\\Plex Media Server\\Plex Media Scanner.exe'
    SQLITE3 = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_PATH))), 'Plug-ins', 'SJVA.bundle', 'pms', 'sqlite3.exe') 
    #SQLITE3 = '%s.exe' % SQLITE3
    PYTHON = 'C:\\Python27\\python.exe'
elif OS == 'MacOSX':
    SCANNER = '/Applications/Plex Media Server.app/Contents/MacOS/Plex Media Scanner'
    SQLITE3 = 'sqlite3'
elif OS == 'Linux':
    if CURRENT_PATH.startswith('/volume'): #synology
        SCANNER = '/var/packages/Plex Media Server/target/Plex Media Scanner'
    else:
        SCANNER = '/usr/lib/plexmediaserver/Plex Media Scanner'
    SQLITE3 = 'sqlite3'


scan_queue = None
filemanager = None
section_list = None


# 현재 실제로 사용하는 것은 0번뿐
def sql_command(sql_type, arg1=''):
    try:
        if sql_type == 0:
            sql = 'update metadata_items set added_at = (select max(added_at) from metadata_items mi where mi.parent_id = metadata_items.id or mi.parent_id in(select id from metadata_items mi2 where mi2.parent_id = metadata_items.id)) where metadata_type = 2'
        elif sql_type == 1:
            sql = 'SELECT library_section_id, root_path FROM section_locations'
        elif sql_type == 'SELECT_FILENAME':
            sql = "SELECT count(*) FROM media_parts WHERE file LIKE '%%%s%%'" % arg1
        command = [SQLITE3, DB, sql]
        Log('Command : %s', command) 
        proc = subprocess.Popen(command)   
        proc.communicate()
        return True 
    except Exception, e: 
        Log('Exception:%s', e)
        Log(traceback.format_exc())
        return None

"""
def load_section_list():
    global section_list
    ret = sql_command(1)
    regex = re.compile(r'(?P<id>^\d+)\|(?P<path>.*?)$', re.MULTILINE)
    section_match = regex.findall(ret)
    section_list = [] 
    for section in section_match:
        section_list.append({'id':section[0].strip(), 'location':unicode(section[1].strip())})
    Log(section_list)
"""
def load_section_list():
    global section_list
    section_list = [] 
    data = JSON.ObjectFromURL('http://127.0.0.1:32400/library/sections')
    for directory in data['MediaContainer']['Directory']:
        for location in directory['Location']:
            section_list.append({'id':directory['key'], 'location':unicode(location['path'].strip()), 'title':directory['title']})
    Log(section_list)

def get_section_title_from_id(key):
    global section_list
    for _ in section_list:
        if _['id'] == key:
            return _['title']

def get_setting(s):
    return Prefs[s]
 
def is_windows():
    return OS == 'Windows'