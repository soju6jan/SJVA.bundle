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

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pms_global
from plex_db import PLEX_DB

logger = pms_global.logger_init(os.path.splitext(os.path.basename(__file__))[0])

class Watchdog(FileSystemEventHandler):
    flag_stop = False
    thread_list = []

    def __init__(self, section_id, section_path):
        logger.debug('__init__')
        logger.debug('ID:[%s] Path:[%s]', section_id, section_path)
        self.section_id = section_id
        if type(self.section_id) == type(u''):
            self.section_id = int(self.section_id)
        self.section_path = section_path
        self.main_thread = None
        self._start_watch_dog()

    def _start_watch_dog(self):
        def thread_function():
            from watchdog.observers.polling import PollingObserver
            observer = PollingObserver()
            logger.debug('observer :%s', observer)
            try:
                observer.schedule(self, self.section_path, recursive=True)
                observer.start()
                logger.debug('WATCHDOG START....%s', self.section_path)
                try:
                    while not self.flag_stop:
                        #logger.debug('111 %s', self.section_path)
                        time.sleep(1)
                except KeyboardInterrupt:
                    observer.stop()
                observer.stop()   
                observer.join()    
            except Exception, e:
                logger.debug(e)
                logger.debug(traceback.format_exc())
        #self.thread = threading.Timer(1.0, thread_function)
        #self.thread = threading.Thread(1.0, thread_function)
        self.main_thread = threading.Thread(target=thread_function, args=())
        self.main_thread.daemon = True
        self.main_thread.start()
        logger.debug('self.therad %s', self.main_thread)

    def stop(self):
        logger.debug('Watchdog stop 1 : %s %s', self.section_path, self.main_thread.isAlive())
        self.flag_stop = True
        self.main_thread.join()
        logger.debug('Watchdog stop 2: %s %s', self.section_path, self.main_thread.isAlive())

    def on_any_event(self, event):
        logger.debug('on_any_event Section:%s is_dir:[%s] type:[%s] path:[%s]', self.section_id, event.is_directory, event.event_type, event.src_path)
        try:
            #p = os.path.dirname(event.src_path)
            # 버그인지 모르겠으나, deleted 시 폴더를 파일로 보내는 경우가 있음.
            # 확장자가 없으면 패스
            tmps = os.path.splitext(event.src_path)
            if tmps[1] == '':
                logger.debug('IGNORE. %s no extension.', event.src_path)
                return
            elif tmps[1][1:] not in pms_global.extension_list:
                logger.debug('IGNORE. %s not in extension list.', event.src_path)
                return
            p = event.src_path                
            #logger.debug('STAT:%s', os.stat(p) )
            # 2019-01-03
            # 파일복사나 외부에서 업로드 되고 있을 경우 created가 먼저 오고, 그 다음 modified 가 온다. 파일복사가 끝난 시점은 알수 없다.
            # created 이벤트가 왔을 때 무조건 보내지 말고, 일단 감시 thread를 하나 만들자
            # 이 thread는 1분에 한번씩 깨어나서, 이전 파일크기와 현재 크기가 다르면 다시1분 대기한다.
            # 이전 크기와 현재 크기가 같다면 api를 호출하고 죽는다.
            s_id = self.section_id
            if self.section_id == -1:
                s_id = PLEX_DB.get_section_id(event.src_path)
                if s_id == -1:
                    logger.debug('IGNORE. %s file section_id is -1.', event.src_path)
                    return
            if not event.is_directory and event.event_type == 'deleted':
                #self.send_command(event.src_path, 'REMOVE')
                if PLEX_DB.is_exist_in_library(event.src_path):
                    pms_global.send_command(s_id, event.src_path, 'REMOVE', 'WATCHDOG')
                else:
                    logger.debug('IGNORE remove. already not in library')
            elif not event.is_directory and event.event_type == 'moved':
                if PLEX_DB.is_exist_in_library(event.src_path) == False:
                    pms_global.send_command(s_id, event.src_path, 'ADD', 'WATCHDOG')
                else:
                    logger.debug('IGNORE. already in library')
                
            elif not event.is_directory and event.event_type in ['created']:
                if PLEX_DB.is_exist_in_library(event.src_path):
                    logger.debug('IGNORE. already in library')
                    return
                for _ in self.thread_list:  
                    if _.file_abspath == event.src_path:
                        logger.debug('WWWWWWWWWWWWWWWhy')
                        return
                logger.debug('Make FileSizeCheckThread')
                t = FileSizeCheckThread()
                t.set_file_abspath(self, s_id, event.src_path)
                t.daemon = True
                t.start()
                self.thread_list.append(t)
            """
            elif not event.is_directory and event.event_type == 'modified':
                for _ in thread_list:
                    if _.file_abspath == event.src_path:
                        _.modified()
                        return
                # thread에 없으면 무시
            """
        except:
            logger.debug(traceback.format_exc())
    
    
    
class FileSizeCheckThread(threading.Thread):
    watchdog_instance = None
    file_abspath = ''
    file_size = 0
    section_id = -1

    def run(self):
        while True:
            time.sleep(60)            
            current_size = os.path.getsize(self.file_abspath)
            if self.file_size == current_size:
                logger.debug('FileSizeCheckThread size match!!')
                #self.watchdog_instance.send_command(self.file_abspath, 'ADD')
                if PLEX_DB.is_exist_in_library(self.file_abspath) == False:
                    pms_global.send_command(self.section_id, self.file_abspath, 'ADD', 'WATCHDOG')
                else:
                    logger.debug('IGNORE. already in library')
                break
            else:
                logger.debug('FileSizeCheckThread size not match %s, %s', self.file_size, current_size)
                self.file_size = current_size

    def set_file_abspath(self, watchdog_instance, section_id, file_abspath):
        self.watchdog_instance = watchdog_instance
        self.section_id = section_id
        self.file_abspath = file_abspath
        self.file_size = os.path.getsize(self.file_abspath)
        logger.debug( 'FILESIZE : %s', self.file_size)



if __name__ == '__main__':
    try:
        logger.debug('Len argv : %s', len(sys.argv))
        logger.debug(sys.argv)
        if len(sys.argv) == 5:
            host = sys.argv[1]
            token = sys.argv[2]
            section_id = int(sys.argv[3])
            try:
                section_root = unicode(sys.argv[4])
            except:
                section_root = sys.argv[4].decode('cp949')

        else:
            host = 'localhost:32400'
            token = ''
            section_id = -1
            section_root = unicode('')
        
        watchdog = Watchdog(host, token, section_id, section_root)
    except Exception, e:
        logger.debug('Exception:%s', e)
        logger.debug(traceback.format_exc())
