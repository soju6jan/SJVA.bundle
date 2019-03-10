# -*- coding: utf-8 -*-
import os
import platform
import sys
import logging
import logging.handlers
import threading
import time
import traceback
import urllib
import urllib2
import json
import platform
import webbrowser

import oauth2client
from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client import tools
from oauth2client.client import flow_from_clientsecrets, OAuth2WebServerFlow
from httplib2 import Http
from oauth2client import file, client, tools
from sqlitedict import SqliteDict

import pms_global
from plex_db import PLEX_DB

reload(sys)
sys.setdefaultencoding('utf-8')
logger = pms_global.logger_init(os.path.splitext(os.path.basename(__file__))[0])


CLIENT_ID = '199519295861-6e7i6g6b2alnd01sh069qu07bids2m6q.apps.googleusercontent.com'
CLIENT_SECRET = '1ft_8smtun3yVPaaNigi-13Z'
SCOPE = 'https://www.googleapis.com/auth/drive'


class GDrive(object):
    current_token_name = None
    current_flow = None
    auth_uri = None

    #plugin에서 호출될수도 있고, 유저가 브라우저에서 호출할수도 있음.
    @classmethod
    def make_token(cls, host, name=None, return_url=False):
        #def thread_function():
            cls.current_token_name = name if name is not None else cls.current_token_name 
            try:
                logger.debug('auth')
                json_file = os.path.join(os.path.dirname(__file__), 'client_secret.json')

                cls.current_flow  = oauth2client.client.flow_from_clientsecrets(
                    json_file,  # downloaded file
                    SCOPE,  # scope
                    #redirect_uri='http://127.0.0.1:35400/gdrive/code')
                    redirect_uri='http://%s/gdrive/code' % host)
                """
                flow = OAuth2WebServerFlow(client_id=CLIENT_ID,
                                        client_secret=CLIENT_SECRET,
                                        scope=SCOPE,
                                        redirect_uri='',
                                        noauth_local_webserver='')
                """
                cls.auth_uri = cls.current_flow.step1_get_authorize_url()
                if return_url:
                    return cls.auth_uri
                else:
                    return webbrowser.open(cls.auth_uri)
                #return True
            except Exception, e:
                logger.debug(e)
                logger.debug(traceback.format_exc())
                return False
        #
        #threading.Timer(1.0, thread_function).start()
        #return True

    @classmethod
    def save_token(cls, code):
        try:
            credentials = cls.current_flow.step2_exchange(code)
            storage = Storage(os.path.join(os.path.dirname(__file__), '%s.json' % cls.current_token_name))
            storage.put(credentials)
            logger.debug('Save token:%s %s',cls.current_token_name, code)
            return True
        except Exception, e:
            logger.debug(e)
            logger.debug(traceback.format_exc())
            return False

    @classmethod
    def make_token_cli(cls, name):
        try:
            json_file = os.path.join(os.path.dirname(__file__), 'client_secret.json')
            current_flow  = oauth2client.client.flow_from_clientsecrets(
                json_file,  # downloaded file
                SCOPE,  # scope
                redirect_uri='urn:ietf:wg:oauth:2.0:oob')
            auth_uri = current_flow.step1_get_authorize_url()
            print("Input url on browser : %s" % auth_uri)
            code = raw_input('Enter code: ')
            credentials = current_flow.step2_exchange(code)
            storage = Storage(os.path.join(os.path.dirname(__file__), '%s.json' % name))
            storage.put(credentials)
            return True
        except Exception, e:
            logger.debug(e)
            logger.debug(traceback.format_exc())
            return False

    """
    @classmethod
    def make_token_cli(cls, name):
        def thread_function():
            try:
                logger.debug('auth')
                flow = OAuth2WebServerFlow(client_id=CLIENT_ID,
                                        client_secret=CLIENT_SECRET,
                                        scope=SCOPE,
                                        redirect_uri='',
                                        noauth_local_webserver='')
                storage = Storage(os.path.join(os.path.dirname(__file__), '%s.json' % name))
                logger.debug('auth1')
                tools.run_flow(flow, storage)
                logger.debug('auth2')
                return True
            except Exception, e:
                logger.debug(e)
                logger.debug(traceback.format_exc())
                return False
        threading.Timer(1.0, thread_function).start()
        return True
    """

    def __init__(self, match_rule):
        #self.match_rule = [u'내 드라이브', u'M:'] soju6janm:내 드라이브,M:
        self.match_rule = match_rule.split(',')
        self.gdrive_name = self.match_rule[0].split(':')[0]
        self.match_rule = [self.match_rule[0].split(':')[1], self.match_rule[1]]
        
        self.db = os.path.join(os.path.dirname(__file__), '%s.db' % self.gdrive_name)
        self.cache = SqliteDict(self.db, tablename='cache', encode=json.dumps, decode=json.loads, autocommit=True)
        self.change_check_interval = 60
        self.api_call_inverval = 5
        self.flag_thread_run = True
        self.thread = None
        self.gdrive_service = None
        #self.match_rule = ['[영화']
        #GdrivePath:내 드라이브/Movie/해외/Blueray/2016/녹투라마 (2016)/nocturama.2016.limited.1080p.bluray.x264-usury.mkv
        

    # 2019-03-10
    # 예) 영화 내부파일을 정리하고 라이브러리 폴더를 옮길 때, 이럴 경우에는 폴더의 이벤트만 오지
    # 파일의 이벤트는 처리하지 않고 있다.
    # 폴더도 처리
    def start_change_watch(self):
        def thread_function():
            store = Storage(os.path.join(os.path.dirname(__file__), '%s.json' % self.gdrive_name))
            creds = store.get()
            if not creds or creds.invalid:
                #flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
                #creds = tools.run_flow(flow, store)
                return -1
            self.gdrive_service = build('drive', 'v3', http=creds.authorize(Http()))
            results = self.gdrive_service.changes().getStartPageToken().execute()
            page_token = results['startPageToken']
            logger.debug('startPageToken:%s', page_token)

            while self.flag_thread_run:
                try:
                    #time.sleep(self.change_check_interval)
                    for _ in range(self.change_check_interval):
                        #logger.debug('%s %s', self.gdrive_name, _)
                        if self.flag_thread_run == False:
                            return
                        time.sleep(1)
                    results = self.gdrive_service.changes().list(
                        pageToken=page_token,
                        fields= "changes( \
                                    file( \
                                        id, md5Checksum,mimeType,modifiedTime,name,parents,teamDriveId,trashed \
                                    ),  \
                                    fileId,removed \
                                ), \
                                newStartPageToken"
                        ).execute()
            
                    page_token = results.get('newStartPageToken')
                    logger.debug('PAGE_TOKEN:%s' % page_token)

                    items = results.get('changes', [])
                    for _ in items:
                        logger.debug('1.CHANGE : %s', _)
                        
                        # 2019-03-10 변경시에는 2개를 보내야 한다.
                        is_add = True
                        is_file = True
                        if _['removed'] == True:
                            is_add = False
                            fileid = _['fileId']
                            if fileid in self.cache:
                                file_meta = {
                                    'name' : self.cache[fileid]['name'],
                                    'parents' : self.cache[fileid]['parents'],
                                    #'mimeType' : self.cache[fileid]['mimeType'],
                                }
                                file_meta['mimeType'] = self.cache[fileid]['mimeType'] if 'mimeType' in self.cache else 'application/vnd.google-apps.folder'
                            else:
                                logger.debug('remove. not cache')
                                continue
                        else:
                            if 'file' in _:
                                if _['file']['mimeType'] == 'application/vnd.google-apps.folder':
                                    logger.debug('FOLDER')
                                elif _['file']['mimeType'].startswith('video'):
                                    logger.debug('FILE')
                                else:
                                    continue
                            fileid = _['file']['id']
                            #삭제시에는 inqueue.. 바로 반영이 될까? RemoveWaitFile만들자
                            #일반적일때는 addwait?                    
                            #logger.debug(u'{0} ({1})'.format(_['file']['name'], _['file']['id']).encode('cp949'))

                            file_meta = self.gdrive_service.files().get(
                                fileId=fileid, fields="id,mimeType, modifiedTime,name,parents,trashed"
                            ).execute()

                        if file_meta['mimeType'] == 'application/vnd.google-apps.folder':
                            is_file = False
                        
                        logger.debug('IS_ADD : %s IS_FILE :%s', is_add, is_file)
                        job_list = []

                        if is_add and is_file:
                            job_list = [[file_meta, 'ADD']]
                        elif is_add and not is_file:
                            job_list = [[file_meta, 'ADD']]
                            #폴더 변경
                            if fileid in self.cache:
                                remove_file_meta = {
                                    'name' : self.cache[fileid]['name'],
                                    'parents' : self.cache[fileid]['parents'],
                                    #'mimeType' : self.cache[fileid]['mimeType'],
                                }
                                remove_file_meta['mimeType'] = self.cache[fileid]['mimeType'] if 'mimeType' in self.cache else 'application/vnd.google-apps.folder'
                                job_list.insert(0, [remove_file_meta, 'REMOVE'])
                        elif not is_add and is_file:
                            job_list = [[file_meta, 'REMOVE']]
                        elif not is_add and not is_file:
                            job_list = [[file_meta, 'REMOVE']]                                              

                        for job in job_list:      
                            file_meta = job[0]
                            type_add_remove = job[1]

                            logger.debug('2.FILEMETA:%s' % file_meta)
                            file_paths = self.get_parent(file_meta)

                            gdrivepath = '/'.join(file_paths)
                            logger.debug('3.GdrivePath:%s' % gdrivepath)
                            mount_abspath = self.get_mount_abspath(file_paths)
                            logger.debug('4.MountPath:%s' % mount_abspath)
                            
                            s_id = PLEX_DB.get_section_id(mount_abspath)
                            if s_id == -1:
                                logger.debug('5-2.IGNORE. %s file section_id is -1.', mount_abspath)
                            else:
                                # 삭제나 변경을 위해서다. 
                                if is_add:
                                    self.cache[fileid] = {
                                        'name': file_meta['name'], 
                                        'parents': file_meta['parents'],
                                        'mimeType' : file_meta['mimeType']
                                    }
                                else:
                                    self.cache[fileid] = None
                                if is_add and not is_file:
                                    try:
                                        if not os.listdir(mount_abspath):
                                            logger.debug('5. IS EMPTY!!')
                                            continue
                                    except:
                                        logger.debug('os.listdir exception!')
                                        pass
                                        
                                if PLEX_DB.is_exist_in_library(mount_abspath) == False:
                                    pms_global.send_command(s_id, mount_abspath, type_add_remove, 'GDRIVE')
                                    logger.debug('5-1.Send Command %s %s %s', s_id, mount_abspath, type_add_remove )
                                else:
                                    logger.debug('5-3.IGNORE. already in library')
                            logger.debug('6.File process end.. WAIT :%s', self.api_call_inverval)
                            for _ in range(self.api_call_inverval):
                                #logger.debug('%s %s', self.gdrive_name, _)
                                if self.flag_thread_run == False:
                                    return
                                time.sleep(1)
                            logger.debug('7.AWAKE Continue')
                except Exception, e:
                    logger.debug('Exception:%s', e)
                    logger.debug(traceback.format_exc())    

        self.thread = threading.Thread(target=thread_function, args=())
        self.thread.daemon = True
        self.thread.start()
        #logger.debug('self.therad %s', self.thread)
        return True

    def get_mount_abspath(self, gdrive_path):
        try:
            replace_gdrive_path = self.match_rule[0].split('/')
            if platform.system() == 'Windows':
            #if os.sep == '\\':
                (drive, p) = os.path.splitdrive(self.match_rule[1])
                replace_mount_path = os.path.split(p)
            else:
                drive = None
                replace_mount_path = os.path.split(self.match_rule[1])

            flag_find = True
            for idx, val  in enumerate(replace_gdrive_path):
                if gdrive_path[idx] != val:
                    flag_find = False
            
            if flag_find:
                ret = u''
                for _ in replace_mount_path:
                    ret = os.path.join(ret, _)
                for _ in gdrive_path[idx+1:]:
                    ret = os.path.join(ret, _)
                if drive is not None:
                    ret = os.path.join(drive, os.sep, ret)
            else:
                ret = None
            return ret
        except Exception, e:
            logger.debug('Exception:%s', e)
            logger.debug(traceback.format_exc())

    def get_parent(self, file_meta):
        file_paths = [file_meta['name']]
        parents = file_meta['parents']
        while parents is not None:
            parent_id = parents[0]
            logger.debug('parent_id:%s', parent_id)
            if parent_id not in self.cache:
                parent_result = self.gdrive_service.files().get(
                    fileId=parent_id, fields="id,mimeType, modifiedTime, name, parents, trashed"
                ).execute()
                #print parent_result #application/vnd.google-apps.folder
                logger.debug('parent_result:%s', parent_result)
                self.cache[parent_id] = {
                    'name': parent_result['name'], 
                    'parents': parent_result['parents'] if 'parents' in parent_result else None,
                    'mimeType' : parent_result['mimeType']
                }
            file_paths.insert(0, self.cache[parent_id]['name'])
            logger.debug('    file_paths:%s', file_paths)
            parents = self.cache[parent_id]['parents']
            logger.debug('    parents:%s', parents)
        return file_paths

    def stop(self):
        logger.debug('Gdrive stop function start..: %s %s ', self.gdrive_name, self.thread.isAlive())
        self.flag_thread_run = False
        self.thread.join()
        logger.debug('Gdrive stop function end..: %s %s', self.gdrive_name, self.thread.isAlive())

if __name__ == '__main__':
    match_rule = 'soju6janw:내 드라이브,M:'
    gdrive = GDrive(match_rule)
    gdrive.start_change_watch()
    gdrive.thread.join()


    if len(sys.argv) == 1:
        sys.argv = [sys.argv[0], 'token', 'test']
    
    if len(sys.argv) == 3:
        name = sys.argv[2]
        token_filename = os.path.join(os.path.dirname(__file__), '%s.json' % name)        
        if sys.argv[1] == 'token':
            sys.argv = [sys.argv[0]]
            if os.path.exists(token_filename):
                os.remove(token_filename)
            if GDrive.make_token_cli(name):
                if os.path.exists(token_filename):             
                    print 'Success!! : %s' % token_filename
                    sys.exit(0)
                else:
                    sys.exit(-1)
            else:
                sys.exit(-1)
    print 'python gdrive.py token [name]'
     
    

    
                
"""
# 내계정에 액세스할 수 있는 앱
#https://myaccount.google.com/u/1/permissions?pageId=none&pli=1

#python 구글 API
#http://www.jinniahn.com/2016/06/blog-post_30.html


#사용자 인증정보
#https://console.cloud.google.com/apis/credentials?project=drive-227120&authuser=3

# 구글에 OAuth2를 이용해서 로그인하고 사용자 정보를 가져오는
# 샘플 코드

#쿼터 제한
#https://console.developers.google.com/iam-admin/quotas?project=drive-227120

# 구글 api scope
# https://developers.google.com/drive/api/v2/about-auth

# API
https://developers.google.com/resources/api-libraries/documentation/drive/v3/python/latest/


"""