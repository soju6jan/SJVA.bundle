# -*- coding: utf-8 -*-
import os
import datetime

class EntityScan(object):
    def __init__(self, section, filename, callback, callback_id, call_from):
        # 파일처리모듈에서 호출, Watchdog, GoogleAPI
        self.wait_status = ''
        self.section_id = section
        self.filename = filename
        self.callback = callback
        self.callback_id = callback_id
        self.call_from = call_from
        self.directory = os.path.dirname(filename)
        self.time_make = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
        self.time_inqueue = ''
        self.time_scan_start = ''
        self.time_scan_end = ''
        self.status = ''
        

    def get_time(self, t):
        if type(t) == 'datetime':
            return t.strftime('%Y-%m-%d %H:%M:%S')   
        else:
            return t

    def get_detail_wait(self):
        status = self.get_status_str()
        ret = [
            '%s %s' % (status, os.path.basename(self.filename)) if Client.Product != 'Plex Web' else '%s %s %s' % (status, self.time_make, os.path.basename(self.filename)),
            '%s' % os.path.dirname(self.filename),
            '추가시간 : %s' % self.time_make,
            '스캔 큐로 이동시간 : %s' % self.time_inqueue
        ]
        return ret

    def get_detail_scan(self):
        ret = self.get_status_str()
        try:
            delta = datetime.datetime.strptime(self.time_scan_end, '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(self.time_scan_start, '%Y-%m-%d %H:%M:%S')
        except:
            delta = '-' 
        detail = [
            ('%s %s' % (ret, os.path.basename(self.filename))).strip() if Client.Product != 'Plex Web' else ('%s %s %s' % (ret, self.time_scan_end, os.path.basename(self.filename))).strip(),
            '%s' % os.path.dirname(self.filename),
            '스캔시작 : %s' % self.time_scan_start,
            '스캔완료 : %s' % self.time_scan_end,
            '진행시간 : %s초' % delta,
            'InQueue시간 : %s' % self.time_inqueue,
            'Wait 추가시간 : %s' % self.time_make
        ] 
        return detail 

    def get_status_str(self):
        if self.status == 'ALREADY':
            ret = '[중복]' 
        elif self.status == 'SCAN_COMPLETED':
            ret = '[완료]'
        elif self.status == 'SCAN_START':
            ret = '[스캔중]'
        elif self.status == 'OK': 
            ret = '[InQueue]' #인큐명령에 의한 대기
        elif self.status == 'EQUAL_FILE':
            ret = '[동일]' 
        elif self.status == 'NO_LIBRARY':
            ret = '[NO_LIB]'
        elif self.status == '': 
            ret = '[대기]' #wait로 인한 대기
        else:
            ret = '[---]'
        if self.call_from == 'GDRIVE':
            ret += 'G'
        elif self.call_from == 'WATCHDOG':
            ret += 'W'
        elif self.call_from == 'FILE_MANAGER':
            ret += 'F'
        #READY_ADD, READY_REMOVE, REAL_ADD, REAL_REMOVE, SHOW_IN_FILELIST
        if self.wait_status == 'READY_ADD':
            ret += ''
        elif self.wait_status == 'READY_REMOVE':
            ret += '(R)'
        #elif self.wait_status == 'REAL_ADD':
        #    ret += '(RA)'            
        elif self.wait_status == 'REAL_REMOVE':
            ret += '(R)'            
        elif self.wait_status == 'SHOW_IN_FILELIST':
            ret += '(E)'            
        elif self.wait_status == 'WRONG_PATH':
            ret = '[WRONG_PATH]'
        elif self.wait_status == 'EXCEPT_PATH':
            ret = '[EXCEPT_PATH]'
        return ret


    def as_dict(self):
        return {
            'wait_status':self.wait_status, 
            'section_id':self.section_id,
            'filename':self.filename, 
            'callback':self.callback, 
            'callback_id':self.callback_id, 
            'call_from':self.call_from, 
            'directory':self.directory,
            'time_make':self.time_make,
            'time_inqueue':self.time_inqueue,
            'time_scan_start':self.time_scan_start,
            'time_scan_end':self.time_scan_end,
            'status':self.status
        }
