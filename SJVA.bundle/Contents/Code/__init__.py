import json
import urllib
import traceback
import sys
import time
import subprocess
import os
import io

import base
from version import VERSION
from entity import EntityScan
from scan_queue import ScanQueue
from file_manager import FileManager
from sjva_pms_handle import SJVA_PMS
from plugin import PluginHandle
from lc import LiveChannels
from tvh import TVHeadend
import unicodedata

NAME = 'SJVA' 
PREFIX = '/video/SJVA'  
ICON = 'icon-default.jpg'        
   
###############################################################
#  plugin
###############################################################
def Start():  
    ObjectContainer.title1 = NAME
    DirectoryObject.thumb = R(ICON) 
    HTTP.CacheTime = 0  
    init()    
  
def init():
    if base.scan_queue is not None:
        base.scan_queue.stop()
    if base.filemanager is not None:
        base.filemanager.stop()
    base.scan_queue = ScanQueue()
    base.filemanager = FileManager()
    base.load_section_list()

@handler(PREFIX, NAME, thumb = ICON)
def MainMenu():
    oc = ObjectContainer()  
    try:
        message = ['<LOG>']  
        for m in message: 
            oc.add(DirectoryObject(key = Callback(MainMenu), title = unicode(m)))
        oc.add(DirectoryObject(key = Callback(WaitList), title = unicode('Wait Log : %s 개' % len(base.filemanager.entity_list))))
        oc.add(DirectoryObject(key = Callback(ScanList), title = unicode('Scan Log : %s 개' % len(base.scan_queue.entity_list))))

        message = ['','<Action>']
        for m in message: 
            oc.add(DirectoryObject(key = Callback(MainMenu), title = unicode(m)))
        ACTION = [ 
            ['RESTART_SCAN_QUEUE', 'A-1. 스캔 정보 초기화'],
            ['RELOAD_SECTION_LIST', 'A-2. 섹션 정보 다시 읽기'],
            ['VIEW_SECTION_LIST', 'A-3. 섹션 정보 확인'], 
            ['PLUG_IN_INSTALL', 'B-1. 플러그인 설치'], 
            ['SELF_UPDATE', 'B-2. 업데이트'], 
            ['SJVA_PMS_START', 'C-1. SJVA Server on PMS 시작'],
        ] 
        for m in ACTION:
            oc.add(DirectoryObject(key = Callback(Action, action_type=m[0]), title = unicode(m[1])))
        status = None
        if SJVA_PMS.is_sjva_pms_run():
            status = SJVA_PMS.get_status()
            ACTION = [      
                ['SJVA_PMS_STOP', 'C-2. SJVA Server on PMS 중지'],
                ['WATCHDOG_START', 'C-3. 드라이브 감시 시작'],
                ['WATCHDOG_STOP', 'C-4. 드라이브 감시  중지'],
                ['GDRIVE_TOKEN', 'C-5. 구글 드라이브 인증'],
                ['GDRIVE_START', 'C-6. 구글 드라이브 감시 시작'],
                ['GDRIVE_STOP', 'C-7. 구글 드라이브 감시 중지'],
            ]
            for m in ACTION:
                oc.add(DirectoryObject(key = Callback(Action, action_type=m[0]), title = unicode(m[1])))
        ACTION = [ 
            ['STREAMING_REFRESH', 'D-1. TVH 채널 업데이트'],
            ['DB_SHOW_ADDED_BY_LAST_EPISODE', 'D-2. DB:쇼 추가 날짜를 최근 에피소드 추가 날짜로'],
            #['DB_CHANGE_SHOW_SCANNER', 'D-3. DB:쇼 스캐너가 Default인 경우 Patch 스캐너로 변경'],
            ['REBOOTING', 'D-3. 리부팅'],
        ] 
        for m in ACTION:
            oc.add(DirectoryObject(key = Callback(Action, action_type=m[0]), title = unicode(m[1])))

        message = [ 
            '',  
            '<Status>',
            ' - Plug-in Version : %s' % VERSION, 
            ' - Server OS : %s & Client.Product : %s' % (Platform.OS, Client.Product),
            #' - SJVA Server on PMS : %s' % (None if SJVA_PMS.sjva_pms_process is None else SJVA_PMS.sjva_pms_process.poll()), 
            ' - SJVA Server on PMS : %s' % ('Not Running' if SJVA_PMS.version is None else SJVA_PMS.version),
            #unicode(' - 현재 %s개 파일 스캔 대기중' % base.scan_queue.scan_queue.qsize()),
            #unicode(' - %s개의 Watchdog 실행중' % len(base.watchdog.process_list)),
            unicode(' - %s개의 Section Location' % ('0' if base.section_list is None else len(base.section_list))),
            unicode(' - %s개의 드라이브 감시 실행중' % (0 if status is None else status['watchdog'])),
            unicode(' - %s개의 구글 드라이브 감시 실행중' % (0 if status is None else status['gdrive'])),    
            #'CURRENT_PATH : %s' % base.CURRENT_PATH,
            #SJVA_PMS.tmp_sjva_pms_process,
        ]
        if Request.Headers['host'].startswith('192') or Request.Headers['host'].startswith('127'):
            message.append(
                ' - HOST : %s & X-Plex-Token : %s' % (Request.Headers['host'], Request.Headers['X-Plex-Token'])
            ) 
        Log(' - HOST : %s' % Request.Headers['host'])
        Log(' - X-Plex-Token : %s' % Request.Headers['X-Plex-Token'])
        for m in message:  
            oc.add(DirectoryObject(key = Callback(MainMenu), title = unicode(m)))
    except Exception as e:
        Log('Exception : %s', e)
        Log(traceback.format_exc()) 
    return oc   
  
@route(PREFIX + '/Action')
def Action(action_type): 
    message = 'Done!!'
    Log('Action_type : %s', action_type)
    if action_type == 'RESTART_SCAN_QUEUE':
        init()
        message = '초기화 되었습니다.'
    elif action_type == 'RELOAD_SECTION_LIST':
        base.load_section_list()
        message = '총 %s개의 라이브러리 폴더' % len(base.section_list)
    elif action_type == 'VIEW_SECTION_LIST':
        oc = ObjectContainer(title2=unicode('섹션 정보'))
        for _ in base.section_list:
            message=unicode('ID:[%s] 라이브러리명:[%s] PATH:[%s]' % (_['id'], _['title'], _['location']))
            oc.add(
                DirectoryObject(
                    key = Callback(Label, message=message), 
                    title=message,
                )
            )
        return oc
    elif action_type == 'PLUG_IN_INSTALL':
        return Plugin()
    elif action_type == 'SELF_UPDATE':
        return Update() 
    elif action_type == 'SJVA_PMS_START':
        if SJVA_PMS.is_sjva_pms_run():
            message = '이미 실행중. 버전:%s' % SJVA_PMS.version
        else:
            SJVA_PMS.start_sjva_pms(base.get_setting('sjva_pms_port'), Request.Headers['host'], Request.Headers['X-Plex-Token'])
            time.sleep(1)
            message = '실행중입니다. 잠시 기다려주세요.'
    elif action_type == 'SJVA_PMS_STOP':
        if SJVA_PMS.is_sjva_pms_run():
            SJVA_PMS.stop()
            message = '곧 중지됩니다.'
        else:
            message = 'Not running!!'
    elif action_type == 'WATCHDOG_START':
        flag_start = False
        count = 0
        try:
            watchdog_path = base.get_setting('watchdog_path')
            for _ in watchdog_path.split('|'):
                SJVA_PMS.watchdog_start(-1, _)
                time.sleep(1)
                count += 1 
            flag_start = True 
        except:   
            Log(traceback.format_exc())  
        if flag_start == False:
            for section in base.section_list:
                SJVA_PMS.watchdog_start(section['id'], section['root'])
                time.sleep(1)
                count += 1
        message = '%s개 드라이브 감시 실행' % count
    elif action_type == 'WATCHDOG_STOP':
        SJVA_PMS.watchdog_stop() 
        message = '곧 중지됩니다.' 
    elif action_type == 'GDRIVE_TOKEN':
        if Client.Product == 'Plex Web':
            ret = SJVA_PMS.gdrive_token(base.get_setting('current_gdrive_name'))
            Log(ret)
            if ret == 'True':
                message = '브라우저에서 인증절차를 진행하세요'
            else:
                message = '브라우저에서 http://PLEX서버IP:%s 으로 접속하세요' % SJVA_PMS.sjva_pms_port
        else:
            message = 'PLEX 서버가 설치되어 있는 기기의 PC 웹에서 실행하세요'
    elif action_type == 'GDRIVE_START':
        Log('gdrive_match_rule : %s', base.get_setting('gdrive_match_rule'))
        count = 0
        try:
            match_rule = base.get_setting('gdrive_match_rule')
            for _ in match_rule.split('|'):
                SJVA_PMS.gdrive_start(_)
                time.sleep(1)
                count += 1 
        except Exception, e:   
            Log('Exception:%s', e)  
            Log(traceback.format_exc())
        message = '%s개 GDrive 감시 실행' % count
    elif action_type == 'GDRIVE_STOP':
        SJVA_PMS.gdrive_stop()
        message = '곧 중지됩니다.' 
    elif action_type == 'STREAMING_REFRESH':
        ret = TVHeadend.init_list()
        message = '%s개 채널 업데이트' % ret
    elif action_type == 'DB_SHOW_ADDED_BY_LAST_EPISODE':
        ret, log = base.sql_command(0)
        if ret:
            message = '업데이트 하였습니다.'
        else: 
            message = '업데이트 에러'
    elif action_type == 'DB_CHANGE_SHOW_SCANNER':
        pass
    elif action_type == 'REBOOTING':
        if base.is_windows():
            command = ['shutdown', '-r', '-f', '-t', '0']
        else:
            command = ['reboot']
        #command = ['explorer']
        Log('Command : %s', command) 
        proc = subprocess.Popen(command)   
        proc.communicate()
    return ObjectContainer(  
        title1 = unicode(L('Action')), 
        header = unicode(L('Action')),   
        message = unicode(L(message))  
    ) 

@route(PREFIX + '/ScanList') 
def ScanList():
    oc = ObjectContainer(title2=unicode('ScanList'))
    for _ in reversed(base.scan_queue.entity_list):
        labels = _.get_detail_scan()
        oc.add(
            DirectoryObject(
                key = Callback(Detail, detail='|'.join(labels)), 
                title=unicode(labels[0]),
            )
        )
    return oc

@route(PREFIX + '/WaitList')
def WaitList(): 
    oc = ObjectContainer(title2=unicode('WaitList'))
    for _ in reversed(base.filemanager.entity_list):
        labels = _.get_detail_wait()
        oc.add( 
            DirectoryObject(
                key = Callback(Detail, detail='|'.join(labels)), 
                title=unicode(labels[0]),
            )
        )
    return oc 

@route(PREFIX + '/Detail')
def Detail(detail):
    labels = detail.split('|')
    oc = ObjectContainer(title2=unicode(labels[0]))
    for _ in labels:
        oc.add(
            DirectoryObject(
                key = Callback(Detail, detail=detail), 
                title=unicode(_), 
            )
        )
    return oc

@route(PREFIX + '/Plugin')
def Plugin():
    oc = ObjectContainer(title2=unicode('플러그인'))
    for _ in PluginHandle.get_list()['list'][1:]:
        oc.add(
            DirectoryObject(
                key = Callback(PluginCheck, title=unicode(_['name']), identifier=_['identifier']), 
                title = unicode(_['name']), 
                summary=unicode(_['description']),
                thumb=_['url_icon']
            )
        )
    return oc 

@route(PREFIX + '/Update')
def Update(force=False):
    if force:
        if SJVA_PMS.is_sjva_pms_run():
            SJVA_PMS.stop()
        ret = PluginHandle.update()
        if ret == 'RUNNING':
            message = '설치 작업이 진행중입니다. 잠시 후 다시 실행해주세요.'
        elif ret == 'ERROR':
            message = 'ERROR'
        elif ret == 'OK':
            message = '업데이트 작업이 시작되었습니다. 재실행 후 버전을 확인하세요.'
        return ObjectContainer(  
            title1 = unicode(L('업데이트')), 
            header = unicode(L('Action')),   
            message = unicode(L(message))  
        )
    else:
        oc = ObjectContainer(title2=unicode('업데이트'))
        message = '업데이트 & 재설치'
        oc.add(DirectoryObject(key = Callback(Update, force=True), title=unicode(message)))
        message = 'Current Version : %s' % VERSION
        oc.add(DirectoryObject(key = Callback(Label, message=message), title=unicode(message)))
        git = PluginHandle.get_git_version()
        start = False
        for _ in git.split('\n'):
            if _ == '"""':
                start = not start
                continue
            if start:
                message = _.strip()
                oc.add(DirectoryObject(key = Callback(Label, message=message), title=unicode(message)))
        return oc

@route(PREFIX + '/PluginCheck')
def PluginCheck(title, identifier, force=False):
    if force == False and PluginHandle.is_plugin_install(identifier):
        oc = ObjectContainer(title2=unicode(title))
        oc.add(
            DirectoryObject(
                key = Callback(Label, message=title),
                title = unicode('이미 설치 되어 있습니다.'), 
            ) 
        )
        oc.add(
            DirectoryObject(
                key = Callback(PluginCheck, title=title, identifier=identifier, force=True),
                title = unicode('재설치'), 
            )
        )
        return oc 
    else:
        ret = PluginHandle.install(identifier)
        if ret == 'RUNNING':
            message = '설치 작업이 진행중입니다. 잠시 후 다시 실행해주세요.'
        elif ret == 'ERROR':
            message = 'ERROR'
        elif ret == 'OK':
            message = '설치 작업이 시작되었습니다. 잠시 기다려 주세요.'
        
        return ObjectContainer(  
            title1 = unicode(L(title)), 
            header = unicode(L('Action')),   
            message = unicode(L(message))  
        )

@route(PREFIX + '/label')
def Label(message):
	oc = ObjectContainer(title2 = unicode(message))
	oc.add(DirectoryObject(key = Callback(Label, message=message),title = unicode(message)))
	return oc

###############################################################
#  API
###############################################################
@route('/version') 
def version():
    return VERSION

@route('/WaitFile')   
def WaitFile(section_id, filename, callback, callback_id, type_add_remove, call_from):
    try:  
        filename = urllib.unquote(filename).decode('euc-kr')
    except UnicodeDecodeError:  
        filename = urllib.unquote(filename)
    ret = base.filemanager.add(section_id, filename, callback, callback_id, type_add_remove, call_from)
    Log('WaitFile %s %s %s %s %s %s', section_id, filename, callback, callback_id, type_add_remove, call_from)
    Response.Headers['Content-Type'] = 'application/json'
    return json.dumps({'ret':ret})  

@route('/Add')   
def Add(filepath):
    try:  
        filepath = urllib.unquote(filepath).decode('euc-kr')
    except UnicodeDecodeError:  
        filepath = urllib.unquote(filepath)
    ret = base.filemanager.add(None, filepath, None, None, 'ADD', 'FILE_MANAGER')
    Log('Add %s', filepath)
    Response.Headers['Content-Type'] = 'application/json'
    return json.dumps({'ret':ret})

@route('/lc')
def lc(sid, ch):
    Log('lc [%s] [%s]', sid, ch)
    Response.Headers['Content-Type'] = 'application/xml; charset=utf-8"'
    return LiveChannels.get_xml(Request.Headers['host'], Request.Headers['X-Plex-Token'], sid, ch)

@route('/lcone')
def lcone(sid, ch, count):
    Log('lcone [%s] [%s] [%s]', sid, ch, count)
    Response.Headers['Content-Type'] = 'application/xml; charset=utf-8"'
    return LiveChannels.get_xml_one(Request.Headers['host'], Request.Headers['X-Plex-Token'], sid, ch, count)

@route('/count_in_library')
def count_in_library(filename):
    try:
        filename = unicodedata.normalize('NFKC', unicode(filename))
        
    except Exception, e: 
        Log('Exception:%s', e)
        #Log(traceback.format_exc())
        try:  
            filename = urllib.unquote(filename).decode('euc-kr')
        except UnicodeDecodeError:  
            filename = urllib.unquote(filename)
    ret, log = base.sql_command('SELECT_FILENAME', filename)
    Log('count_in_library [%s] %s', filename, log)
    return log

@route('/db_handle')
def db_handle(action, args):
    try:
        args = unicodedata.normalize('NFKC', unicode(args))
    except Exception, e: 
        Log('Exception:%s', e)
        #Log(traceback.format_exc())
        try:  
            args = urllib.unquote(args).decode('euc-kr')
        except UnicodeDecodeError:  
            args = urllib.unquote(args)
    ret, log = base.sql_command(action, args)
    Log('db_handle [%s:%s] %s', action, args, log)
    return log
 
@route('/os_path_exists')
def os_path_exists(filepath):
    try:
        filepath = unicodedata.normalize('NFKC', unicode(filepath))
    except Exception, e: 
        try:  
            filepath = urllib.unquote(filepath).decode('euc-kr')
        except UnicodeDecodeError:  
            filepath = urllib.unquote(filepath)
    return str(os.path.exists(filepath))




### TVH
#http://%s/:/plugins/com.plexapp.plugins.SJVA/function/tvhm3u?X-Plex-Token=%s
@route('/tvhm3u')
def tvhm3u(): 
    return TVHeadend.tvhm3u(Request.Headers['host'], Request.Headers['X-Plex-Token'])

@route('/tvhurl')
def tvhurl(key, streaming_type):
    return TVHeadend.tvhurl(key, streaming_type, Request.Headers['host'], Request.Headers['X-Plex-Token'])

###############################################
#From SJVA Server on PMS
@route('/SJVA_START')  
def SJVA_START(version): 
    Log('SJVA_START : %s', version)
    SJVA_PMS.sjva_pms_process = SJVA_PMS.tmp_sjva_pms_process
    SJVA_PMS.version = version
    return json.dumps({'ret':'ok'}) 


# 2018-08-14
@route('/command')
def command(cmd, param1, param2): 
    ret = {}
    try:
        ret['ret'] = 'wrong_command'
        if cmd == 'get_scan_wait_list':
            ret['data'] = []
            for _ in reversed(base.filemanager.entity_list):
                ret['data'].append(_.as_dict())
        elif cmd == 'get_scan_completed_list':
            ret['data'] = []
            for _ in reversed(base.scan_queue.entity_list):
                ret['data'].append(_.as_dict())
        elif cmd == 'restart_scan_queue':
            init()
        elif cmd == 'reload_section':
            base.load_section_list()
            ret['data'] = str(len(base.section_list))
        elif cmd == 'get_setcion':
            ret['data'] = []
            for _ in base.section_list:
                ret['data'].append({'id':_['id'], 'title':_['title'], 'location':_['location']})
        elif cmd == 'self_update':
            ret['data'] = PluginHandle.update()
        elif cmd == 'install_plugin':
            identifier = param1
            ret['data'] = PluginHandle.install(identifier)
        elif cmd == 'install_plugin_confirm':
            identifier = param1
            ret['data'] = PluginHandle.is_plugin_install(identifier)
        elif cmd == 'get_plugin_list':
            ret['data'] = []
            for _ in PluginHandle.get_list()['list'][1:]:
                ret['data'].append({'name':_['name'], 'identifier':_['identifier'], 'description':_['description'], 'icon':_['url_icon']})
        elif cmd == 'get_log':
            tmps = param1.split('/')
            Log(tmps)
            filename = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(base.CURRENT_PATH))))
            # 2020-03-05 by rbits
            if base.OS == 'SHIELD':
                filename = filename.replace('/storage/emulated/0/Android/data/com.plexapp.mediaserver.smb', '/storage/emulated/0')
            for x in tmps:
                filename = os.path.join(filename, x)
            Log(filename)
            if os.path.exists(filename):
                data = io.open(filename, 'r', encoding="utf8").read()
                Log(data)
                ret['data'] = data
            else:
                ret['data'] = 'wrong_filename'
        ret['ret'] = 'success' 
    except Exception, e: 
        Log('Exception:%s', e)
        ret['ret'] = 'exception'
        ret['data'] = str(e)
    return json.dumps(ret) 