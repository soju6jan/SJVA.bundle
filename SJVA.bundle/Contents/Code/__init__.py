import json
import urllib
import traceback
import sys
import time
    
import base
from entity import EntityScan
from scan_queue import ScanQueue
from file_manager import FileManager
from sjva_pms_handle import SJVA_PMS
from plugin import PluginHandle
from lc import LiveChannels
from tvh import TVHeadend

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
            ['DB_CHANGE_SHOW_SCANNER', 'D-3. DB:쇼 스캐너가 Default인 경우 Patch 스캐너로 변경'],
            ['REBOOTING', 'D-4. 리부팅'],
        ] 
        for m in ACTION:
            oc.add(DirectoryObject(key = Callback(Action, action_type=m[0]), title = unicode(m[1])))

        message = [ 
            '',  
            '<Status>',
            ' - Plug-in Version : %s' % base.VERSION, 
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
    elif action_type == 'PLUG_IN_INSTALL':
        return Plugin()
    elif action_type == 'SELF_UPDATE':
        pass 
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
        Log('use_all_library : %s', base.get_setting('use_all_library'))
        flag_start = False
        count = 0
        if base.get_setting('use_all_library') == False:
            try:
                watchdog_path = base.get_setting('watchdog_path')
                for _ in watchdog_path.split('|'):
                    SJVA_PMS.watchdog_start(-1, _)
                    time.sleep(1)
                    count += 1 
                flag_start = True 
            except:   
                Log('use_all_library false exception')
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
        ret = base.sql_command(0)
        if ret:
            message = '업데이트 하였습니다.'
        else:
            message = '업데이트 에러'
    elif action_type == 'DB_CHANGE_SHOW_SCANNER':
        pass
    elif action_type == 'REBOOTING':
        pass

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
    for _ in PluginHandle.get_list()['list']:
        oc.add(
            DirectoryObject(
                key = Callback(PluginCheck, title=unicode(_['name']), identifier=_['identifier']), 
                title = unicode(_['name']), 
                summary=unicode(_['description']),
                thumb=_['url_icon']
            )
        )
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
    return base.VERSION

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

### TVH
#http://%s/:/plugins/com.plexapp.plugins.SJVA/function/tvhm3u?X-Plex-Token=%s
@route('/tvhm3u')
def tvhm3u():
    return TVHeadend.tvhm3u(Request.Headers['host'], Request.Headers['X-Plex-Token'])

@route('/tvhfile')
def tvhfile(key):
    return TVHeadend.tvhfile(key, Request.Headers['host'], Request.Headers['X-Plex-Token'])

###############################################
#From SJVA Server on PMS
@route('/SJVA_START')  
def SJVA_START(version): 
    Log('SJVA_START : %s', version)
    SJVA_PMS.sjva_pms_process = SJVA_PMS.tmp_sjva_pms_process
    SJVA_PMS.version = version
    return json.dumps({'ret':'ok'}) 

