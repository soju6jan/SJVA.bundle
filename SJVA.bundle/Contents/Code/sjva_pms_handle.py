# -*- coding: utf-8 -*-
import os
import urllib
import urllib2
import traceback
import subprocess
import json
import base
 
HOST = '127.0.0.1'
SJVA_PMS_PY = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(base.CURRENT_PATH))), 'Plug-ins', 'SJVA.bundle', 'pms', 'sjva_pms.py') 

class SJVA_PMS(object): 
    flag_start_sjva = False
    sjva_pms_process = None
    sjva_pms_port = base.get_setting('sjva_pms_port') #35400' #None
    tmp_sjva_pms_process = None
    version = None

    @classmethod
    def start_sjva_pms(cls, port, host, token): 
        cls.flag_start_sjva = True
        Log('Start SJVA PMS Port: %s', port)
        try:    
            command = '"%s" "%s" "%s" "%s" "%s"' % (base.PYTHON, SJVA_PMS_PY, port, host, token)
            Log(command) 
            if base.is_windows():
                cls.tmp_sjva_pms_process = subprocess.Popen(command, shell=True)
            else:
                cls.tmp_sjva_pms_process = subprocess.Popen(command, shell=True, env={"PYTHONIOENCODING":"utf-8", "PYTHONPATH": ".", "LANG":"en_US.UTF-8"}) 
                # ANSI_X3.4-1968 sys.stdout.encodeing 
                # LANG이 설정되어야..    
            Log('process :%s', cls.tmp_sjva_pms_process)  
        except Exception, e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())

    @classmethod
    def is_sjva_pms_run(cls):
        if cls.flag_start_sjva == False:
            return False
        if cls.version is not None:
            return True
        if cls.get_version() == None:
            return False
        else: 
            return True

    @classmethod    
    def get_version(cls):
        try:
            url = 'http://%s:%s/version' % (HOST, cls.sjva_pms_port)
            Log('get_version : %s', url)
            postdata = ''
            request = urllib2.Request(url)
            response = urllib2.urlopen(request) 
            data = response.read()
            Log('get_version : %s', data)
            return data
        except Exception, e:  
            Log('Exception:%s', e) 
            Log('Known Error. not running SJVA Server on PMS')
            #Log(traceback.format_exc())
            return None  

    @classmethod     
    def get_status(cls):
        try:
            url = 'http://%s:%s/status' % (HOST, cls.sjva_pms_port)
            Log('get_status : %s', url)
            request = urllib2.Request(url)
            response = urllib2.urlopen(request) 
            data = response.read()
            data = json.loads(data)
            Log('get_status : %s', data)
            return data
        except Exception, e:  
            Log('Exception:%s', e) 
            Log(traceback.format_exc())
            return None  

    @classmethod  
    def stop(cls): 
        Log('Stop SJVA PMS Port')  
        try:
            url = 'http://%s:%s/kill' % (HOST, cls.sjva_pms_port)
            Log('stop : %s', url)
            request = urllib2.Request(url)
            response = urllib2.urlopen(request)
            data = response.read()
            Log('stop : %s', data)
            cls.sjva_pms_process.terminate()
            cls.sjva_pms_process.kill() 
            return data
        except Exception, e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
        finally:
            cls.sjva_pms_process = None
            cls.version = None    
  
     
    @classmethod  
    def watchdog_start(cls, section_id, section_path):
        try:
            url = 'http://%s:%s/watchdog/start' % (HOST, cls.sjva_pms_port)
            Log('start_watchdog : %s %s', section_id, section_path)
            params = { 'section_id' : section_id, 'section_path' : section_path }
            postdata = urllib.urlencode( params ) 
            request = urllib2.Request(url, postdata)
            response = urllib2.urlopen(request) 
            data = response.read()
            Log('start_watchdog ret : %s', data)
            return data
        except Exception, e:  
            Log('Exception:%s', e)  
            Log(traceback.format_exc())
            return None
    
    @classmethod  
    def watchdog_stop(cls):
        try:
            url = 'http://%s:%s/watchdog/stop' % (HOST, cls.sjva_pms_port)
            Log('watchdog_start') 
            params = {}
            postdata = urllib.urlencode( params ) 
            request = urllib2.Request(url, postdata)
            response = urllib2.urlopen(request) 
            data = response.read()
            Log('watchdog_start ret : %s', data)
            return data
        except Exception, e:  
            Log('Exception:%s', e)  
            Log(traceback.format_exc())
            return None 

    # GDrive token 
    @classmethod   
    def gdrive_token(cls, token_name):
        try: 
            url = 'http://%s:%s/gdrive/token' % (HOST, cls.sjva_pms_port)
            Log('gdrive/token : %s', token_name)
            params = { 'token_name' : token_name }
            postdata = urllib.urlencode( params ) 
            request = urllib2.Request(url, postdata)
            response = urllib2.urlopen(request) 
            data = response.read()
            Log('gdrive/token ret : %s', data)
            return data
        except Exception, e:  
            Log('Exception:%s', e)  
            Log(traceback.format_exc())
            return None
    
    
    @classmethod   
    def gdrive_start(cls, match_rule):
        try: 
            url = 'http://%s:%s/gdrive/start' % (HOST, cls.sjva_pms_port)
            Log('gdrive/start : %s', match_rule)
            params = { 'match_rule' : match_rule }
            postdata = urllib.urlencode( params ) 
            request = urllib2.Request(url, postdata)
            response = urllib2.urlopen(request) 
            data = response.read()
            Log('gdrive/start ret : %s', data)
            return data
        except Exception, e:  
            Log('Exception:%s', e)  
            Log(traceback.format_exc())
            return None  
    
    # GDrive token   
    @classmethod   
    def gdrive_stop(cls):
        try: 
            url = 'http://%s:%s/gdrive/stop' % (HOST, cls.sjva_pms_port)
            Log('gdrive/stop')
            params = { }
            postdata = urllib.urlencode( params ) 
            request = urllib2.Request(url, postdata)
            response = urllib2.urlopen(request) 
            data = response.read()
            Log('gdrive/stop ret : %s', data)
            return data
        except Exception, e:  
            Log('Exception:%s', e)  
            Log(traceback.format_exc())
            return None
