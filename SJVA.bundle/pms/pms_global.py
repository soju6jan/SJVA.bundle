# -*- coding: utf-8 -*-
import os
import logging
import logging.handlers
from flask import Flask
import urllib
import urllib2
import traceback

VERSION = '0.0.0.1'
PLEX_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
DB_FILE = os.path.join(PLEX_ROOT, 'Plug-in Support', 'Databases', 'com.plexapp.plugins.library.db')

post = None
#host = '127.0.0.1:32400'
#token = 'nPGFrj6p8sWzuNNgasYW'
host = None
token = None
watchdog_list = []
current_flow = None
current_token_name = None
gdrive_list = []

extension_list = ['webm', 'mkv', 'flv', 'vob', 'ogv', 'ogg', 'drc', 'gif', 'gifv', 'mng',
    'avi', 'mov', 'qt', 'wmv', 'yuv', 'rm', 'rmvb', 'asf', 'amv', 'mp4', 'm4p',
    'm4v', 'mpg', 'mp2', 'mpeg', 'mpe', 'mpv', 'm2v', 'm4v', 'svi', '3gp',
    '3g2', 'mxf', 'roq', 'nsv', 'f4v', 'f4p', 'f4a', 'f4b', 'mp3', 'flac', 'ts',
    'srt', 'smi', 'ass', 'ssa', 'sami', 'usf', 'vtt', 'sub',
    'heic', 'jpg', 
]


def logger_init(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(u'[%(asctime)s|%(levelname)s|%(filename)s:%(lineno)s] : %(message)s')
    file_max_bytes = 10 * 1024 * 1024 
    #filename=os.path.join(os.path.dirname(__file__), '%s.log' % os.path.splitext(os.path.basename(__file__))[0])
    filename=os.path.join(os.path.dirname(__file__), '%s.log' % name)
    fileHandler = logging.handlers.RotatingFileHandler(filename=filename, maxBytes=file_max_bytes, backupCount=5, encoding='utf8')
    streamHandler = logging.StreamHandler() 
    fileHandler.setFormatter(formatter)
    streamHandler.setFormatter(formatter) 
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)
    return logger

logger = logger_init(os.path.splitext(os.path.basename(__file__))[0])


def send_command(section_id, filename, type_add_remove, call_from):
    try:
        #url = 'http://%s/:/plugins/com.plexapp.plugins.SJVA/function/InQueue?section_id=%s&filename=%s&X-Plex-Token=%s' % (pms_global.host, self.section_id, urllib.quote(filename.encode('cp949')), pms_global.token)
        url = 'http://%s/:/plugins/com.plexapp.plugins.SJVA/function/WaitFile?section_id=%s&filename=%s&callback=%s&callback_id=%s&type_add_remove=%s&call_from=%s&X-Plex-Token=%s' % (host, section_id, urllib.quote(filename.encode('cp949')), '', '', type_add_remove, call_from, token)
        logger.debug('- URL:%s', url)
        logger.debug('- send_command section_id:[%s], file[%s]', section_id, filename)
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        data = response.read()
        logger.debug('- send_command Result : %s', data)
    except Exception, e:
        logger.debug('Exception:%s', e)
        logger.debug(traceback.format_exc())
            


if __name__ == '__main__':
    logger = logger_init(os.path.splitext(os.path.basename(__file__))[0])
