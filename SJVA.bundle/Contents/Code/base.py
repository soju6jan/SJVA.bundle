# -*- coding: utf-8 -*-
import os
import re
import traceback
import subprocess
import sys
import threading

try:
    sys.setdefaultencoding('utf-8')
except:
    Log('setdefaultencoding fail!!')

OS = Platform.OS
CURRENT_PATH = re.sub(r'^\\\\\?\\', '', os.getcwd())
DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_PATH))), 'Plug-in Support', 'Databases', 'com.plexapp.plugins.library.db')

PYTHON = 'python'       
if OS == 'Windows':
    SCANNER = r'C:\\Program Files (x86)\\Plex\\Plex Media Server\\Plex Media Scanner.exe'
    SQLITE3 = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_PATH))), 'Plug-ins', 'SJVA.bundle', 'pms', 'sqlite3.exe') 
    PYTHON = 'C:\\Python27\\python.exe'
elif OS == 'MacOSX':
    SCANNER = '/Applications/Plex Media Server.app/Contents/MacOS/Plex Media Scanner'
    SQLITE3 = 'sqlite3'
elif OS == 'Linux':
    if CURRENT_PATH.startswith('/volume'): #synology
        SCANNER = '/var/packages/Plex Media Server/target/Plex Media Scanner'
    else:
        # 2020-03-05 by rbits
        if os.path.exists('/storage/emulated'):
            OS = 'SHIELD'
            SCANNER = '/data/user/0/com.plexapp.mediaserver.smb/Resources/Plex Media Scanner'
        else:
            SCANNER = '/usr/lib/plexmediaserver/Plex Media Scanner'
    SQLITE3 = 'sqlite3'


SQLITE3_NEW = [SCANNER.replace('Scanner', 'Server'), '--sqlite']
if OS == 'Windows': #18 왜?
    SQLITE3_NEW[1] = '-sqlite'


scan_queue = None
filemanager = None
section_list = None


# 현재 실제로 사용하는 것은 0번뿐
def sql_command(sql_type, arg1=''):
    try:
        if sql_type == 0:
            if OS == 'SHIELD':
                return False, ''
            sql = 'update metadata_items set added_at = (select max(added_at) from metadata_items mi where mi.parent_id = metadata_items.id or mi.parent_id in(select id from metadata_items mi2 where mi2.parent_id = metadata_items.id)) where metadata_type = 2;'
            #command = [SQLITE3, DB, sql]
            command = SQLITE3_NEW + [DB, sql]
        elif sql_type == 1:
            sql = 'SELECT library_section_id, root_path FROM section_locations;'
            command = [SQLITE3, DB, sql]
        elif sql_type == 'SELECT_FILENAME':
            if OS == 'SHIELD':
                return True, '0'
            sql = u"SELECT count(*) FROM media_parts WHERE file LIKE '%%%s%%';" % arg1
            from io import open
            with open("select.sql", "wb") as output:
                output.write(sql)
            command = [SQLITE3, DB, '.read select.sql']
        elif sql_type == 'get_metadata_id_by_filepath':
            sql = u"SELECT metadata_item_id FROM media_items WHERE id = (SELECT media_item_id FROM media_parts WHERE file = '%s');" % arg1
            from io import open
            with open("select.sql", "wb") as output:
                output.write(sql)
            command = [SQLITE3, DB, '.read select.sql']
        elif sql_type == 'get_filepath_list_by_metadata_id':
            sql = u"SELECT file FROM media_parts, media_items, metadata_items WHERE media_parts.media_item_id = media_items.id and media_items.metadata_item_id = metadata_items.id and metadata_items.id = %s ORDER BY media_parts.created_at;" % arg1
            from io import open
            with open("select.sql", "wb") as output:
                output.write(sql)
            command = [SQLITE3, DB, '.read select.sql'] 

        Log('Command : %s', command) 
        #proc = subprocess.Popen(command)
        p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
        out, err = p.communicate() 
        return True, out.strip()
    except Exception, e: 
        Log('Exception:%s', e)
        Log(traceback.format_exc())
        return None

def sql_command2(query):
    try:
        query += ';'
        from io import open
        with open("query.sql", "wb") as output:
            output.write(query)
        # '.read query.sql' => 두개로 분리하지 말것. 
        if query.lower().startswith('select'):
            command = [SQLITE3, DB, '.read query.sql']
        else:
            # 파일에서 읽는거 확인
            command = SQLITE3_NEW + [DB, '.read query.sql']
            #command = SQLITE3_NEW + [DB, u'%s' % query]

        Log('Command : %s', command) 
        p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
        out, err = p.communicate()
        return True, out.strip().split('\n')
    except Exception, e: 
        Log('Exception:%s', e)
        Log(traceback.format_exc())
        return False, ''
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
    section_list = sorted(section_list, key=lambda itm: len(itm['location']), reverse=True)
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

