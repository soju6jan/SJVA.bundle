# -*- coding: utf-8 -*-
import os
import re
import Queue
import threading
import datetime
import time
import subprocess
from threading import Lock
import traceback
import urllib
import urllib2
import base
from entity import EntityScan

class ScanQueue(object): 
    scan_thread = None 
    scan_queue = None  
    current_scan_entity = None
    flag_stop = False
    current_scan_t = None

    def __init__(self):
        self.inqueue_mutex = Lock()
        self.entity_list = []
        self.start_scan_queue()  
        self.wait_event = threading.Event()
    
      
    ###############################################################
    #  스캔 모듈
    ###############################################################
    def start_scan_queue(self):
        self.scan_queue = Queue.Queue()
        self.scan_thread = threading.Thread(target=self.scan_queue_thread, args=())
        self.scan_thread.daemon = True  
        self.scan_thread.start()
        Log('Start.. Scan Queue!!') 
    
    def stop(self):
        Log('scanqueue stop!! %s', self.current_scan_t)
        if self.current_scan_t is not None:
            self.current_scan_t.join()
        if self.scan_thread is not None:
            self.flag_stop = True
            self.scan_queue.put(None)
            self.scan_thread.join()
        #self.start_scan_queue()
        Log('Stop Scan Queue!!')
        #scan_t 로 죽여야하는데..

    def scan_queue_thread(self):
        while self.flag_stop == False:
            Log('* 스캔 큐 대기 : %s', self.scan_queue.qsize())
            self.current_scan_entity = self.scan_queue.get()
            # 초기화
            if self.current_scan_entity is None:
                return
            Log('* 스캔 큐 AWAKE : %s', self.current_scan_entity.filename)
            self.current_scan_entity.status = 'SCAN_START' 
            
            self.current_scan_entity.scan_start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            Log('* 스캔 큐 scan_start_time : %s', self.current_scan_entity.scan_start_time)
            
            #self.scan_start(self.current_scan_entity)
            self.current_scan_t = ScanThread()
            self.current_scan_t.set(self.current_scan_entity, self.wait_event)
            self.current_scan_t.start()
            Log('* 스캔 큐 thread 종료 대기')
            self.wait_event.wait()
            self.current_scan_t = None
            # 초기화 한번 체크
            if self.flag_stop: return
            self.current_scan_entity.status = 'SCAN_COMPLETED' 
            self.current_scan_entity.scan_end_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.scan_queue.task_done()
            Log('* 남은 큐 사이즈 : %s', self.scan_queue.qsize())
            self.current_scan_entity = None
            time.sleep(2) 
    """
    def add(self, section_id, filename):
        entity = EntityScan(1, section_id, filename, None, None)
        return self.in_queue(entity)
    """

    def in_queue(self, entity):
        # 24시간 지난 목록 제거. thread가 아니라 queue 동작하기에 이곳에 넣는다
        for _ in self.entity_list:
            delta = datetime.datetime.strptime(_.time_inqueue, '%Y-%m-%d %H:%M:%S') - datetime.datetime.now()
            if delta.days > 1:
                self.entity_list.remove(_)

        try:
            self.inqueue_mutex.acquire()
            Log('INQUEUE current SECTION ID :%s', entity.section_id)
            if entity.section_id is None or entity.section_id == '':
                for _ in base.section_list: 
                    if entity.filename.find(_['location']) != -1:
                        entity.section_id = _['id']  
                        break 
                if entity.section_id is None or entity.section_id == '':
                    entity.status = 'NO_LIBRARY'  
                    return entity.status 
            Log('INQUEUE after SECTION ID :%s', entity.section_id)
            #self.entity_list.append(entity)  
            for _ in list(self.scan_queue.queue):
                if _.directory == entity.directory:
                    entity.status = 'ALREADY' 
                    return entity.status
                    
            if self.current_scan_entity is not None and entity.filename == self.current_scan_entity.filename:
                entity.status = 'EQUAL_FILE'
                #self.entity_list.pop()
                return entity.status
            entity.time_inqueue = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
            self.entity_list.append(entity) 
            Log('In queue - section:[%s] filename:[%s]', entity.section_id, entity.filename)
            entity.status = 'OK' 
            self.scan_queue.put(entity)
            Log('In queue - qsize : %s', self.scan_queue.qsize())
            return entity.status 
        except Exception, e:
            entity.status = str(e)
            return entity.status 
        finally:
            self.inqueue_mutex.release()
            time.sleep(1)

class ScanThread(threading.Thread):
    entity = None
    wait_event = None
    
    def set(self, entity, wait_event):
        self.entity = entity
        self.wait_event = wait_event

    def run(self):
            try: 
                Log('Scan START - section:[%s] filename:[%s]', self.entity.section_id, self.entity.filename)
                self.entity.time_scan_start = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
                #command = '"%s" --scan --refresh --section %s --directory "%s"' % (base.SCANNER, self.entity.section_id, self.entity.directory.encode('cp949'))
                #command = '"%s" --scan --refresh --section %s' % (base.SCANNER, self.entity.section_id)
                #command = [base.SCANNER, '--scan', '--refresh', '--section', self.entity.section_id, '--directory', self.entity.directory.encode('cp949')]
                tmp = self.entity.directory.encode('cp949') if base.is_windows() else self.entity.directory
                command = [base.SCANNER, '--scan', '--refresh', '--section', self.entity.section_id, '--directory', tmp]
                proc = subprocess.Popen(command)   
                try:
                    #proc.communicate(timeout=10*60) 
                    proc.wait()
                except Exception as e:
                    Log('EXCEPTION:::: %s', e)
                    proc.kill() 
                    #outs, errs = proc.communicate()
                
                #Log('스캔 시작')
                #proc.wait()
                Log('스캔 종료')
                if base.get_setting('use_recent_episode_at_show_dated'):
                    result = base.sql_command(0) 
            
                host = []
                if self.entity.callback is not None and self.entity.callback != '':
                    host = [self.entity.callback]
                elif base.get_setting('sjva_callback') is not None and base.get_setting('sjva_callback') != '':
                    host = base.get_setting('sjva_callback').split('|')
                Log('CALLBACK HOST:%s', host) 
                for _ in host:
                    try:
                        #url = 'http://%s/api/scan_complete' % _
                        url = _
                        params = { 'filename' : self.entity.filename, 'id' : self.entity.callback_id }
                        postdata = urllib.urlencode( params ) 
                        request = urllib2.Request(url, postdata)
                        response = urllib2.urlopen(request)
                        Log('CALLBACK RET : %s', response.read())    
                    except:
                        Log(traceback.format_exc())
                self.entity.time_scan_end = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
                Log('Scan END')
            except Exception, e: 
                Log('Exception:%s', e)
                Log(traceback.format_exc())
            finally:
                if self.wait_event is not None:
                    self.wait_event.set()
    