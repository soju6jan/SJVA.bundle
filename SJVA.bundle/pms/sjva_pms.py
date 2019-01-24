# -*- coding: utf-8 -*-
import os
import sys

import traceback
import threading
import urllib2
import requests
import time
from flask import Flask, jsonify, request, redirect

import pms_global
from plex_db import PLEX_DB
from pms_watchdog import Watchdog
from gdrive import GDrive

reload(sys)
sys.setdefaultencoding('utf-8')

logger = pms_global.logger_init(os.path.splitext(os.path.basename(__file__))[0])
pms_global.app = Flask(__name__)

###############################################################
#  Route
###############################################################
@pms_global.app.route('/', methods=['GET', 'POST'])
@pms_global.app.route('/version', methods=['GET', 'POST'])
def route_home():
    return pms_global.VERSION

@pms_global.app.route('/db/<sub>', methods=['GET', 'POST'])
def route_db(sub):
    logger.debug('route_db:%s' % sub)
    try:
        if sub == 'GET_SECTION_LIST':
            ret = PLEX_DB.get_section_list()
        return jsonify({'ret':'ok', 'data':ret})
    except Exception, e:
        logger.debug(e)
        logger.debug(traceback.format_exc())
        return jsonify({'ret':'fail'})

@pms_global.app.route('/watchdog/<sub>', methods=['GET', 'POST'])
def route_watchdog(sub):
    logger.debug('route_watchdog:%s' % sub)
    if sub == 'start':
        if request.method == 'POST':
            section_id = request.form['section_id']
            section_path = request.form['section_path']
            logger.debug('section_id : %s', section_id)
            logger.debug('section_path : %s', section_path)
            pms_global.watchdog_list.append(Watchdog(section_id, section_path))
    elif sub == 'stop':
        for watchdog in pms_global.watchdog_list:
            watchdog.stop()
        pms_global.watchdog_list = []
    return 'ok'

@pms_global.app.route('/gdrive/<sub>', methods=['GET', 'POST'])
def route_gdrive(sub):
    logger.debug('route_gdrive:%s' % sub)
    if sub == 'token':
        if request.method == 'POST':
            token_name = request.form['token_name']
            logger.debug('token:%s', token_name)
            ret = GDrive.make_token(request.host, name=token_name)
            return str(ret)
    elif sub == 'code':
        code = request.args.get('code')
        if GDrive.save_token(code):
            return u'토큰이 저장되었습니다'
    elif sub == 'start':
        if request.method == 'POST':
            match_rule = request.form['match_rule']
            logger.debug('match_rule:%s', match_rule)
            gdrive = GDrive(match_rule)
            gdrive.start_change_watch()
            pms_global.gdrive_list.append(gdrive)
    elif sub == 'stop':
        for _ in pms_global.gdrive_list:
            _.stop()
        pms_global.gdrive_list = []
    
    return 'ok'

# 그지같지만 어쩔수가 없다. 로컬 IP가 안된다
# 이 방법이 안되면 어쩔수 없이 cli로 한다
# 1. 사용자 로컬IP:35400/token 접속
# 2. 리다이렉트를 plex API로
# 그냥 CLI로..
"""
@pms_global.app.route('/token', methods=['GET', 'POST'])
def route_token():
    tmp = request.host.split(':')
    host = ':'.join([tmp[0]+'.xip.io', tmp[1]])
    url = GDrive.make_token(host, return_url=True)
    logger.debug('TOKEN Redirect :%s', url)
    #tmp = GDrive.auth_uri.replace('127.0.0.1', request.host.split(':')[0])
    return redirect(url, code=302)
"""
@pms_global.app.route('/status', methods=['GET', 'POST'])
def route_status():
    logger.debug('route_status')
    ret = {
        'version':pms_global.VERSION,
        'watchdog':len(pms_global.watchdog_list),
        'gdrive':len(pms_global.gdrive_list),
    }
    return jsonify(ret)
###############################################################


###############################################################
#  시작 & 종료
###############################################################
def send_start_noti(flag_test):
    def threand_fuction():
        try:
            logger.debug('send_start_noti')
            url = 'http://%s/:/plugins/com.plexapp.plugins.SJVA/function/SJVA_START?version=%s&X-Plex-Token=%s' % (pms_global.host, pms_global.VERSION, pms_global.token)
            request = urllib2.Request(url)
            response = urllib2.urlopen(request) 
            data = response.read()
            logger.debug('send_start_noti : %s', data)
        except Exception, e:
            if flag_test == False:
                logger.debug('Exception:%s', e) 
                logger.debug(traceback.format_exc())
    t = threading.Thread(target=threand_fuction, args=())
    t.start()
    PLEX_DB.init()

LAST_REQUEST_MS = 0
@pms_global.app.before_request
def update_last_request_ms():
    global LAST_REQUEST_MS
    LAST_REQUEST_MS = time.time() * 1000

@pms_global.app.route('/seriouslykill', methods=['POST'])
def seriouslykill():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return "Shutting down..."

@pms_global.app.route('/kill', methods=['GET', 'POST'])
def kill():
    last_ms = LAST_REQUEST_MS
    def shutdown():
        if LAST_REQUEST_MS <= last_ms:  # subsequent requests abort shutdown
            requests.post('http://localhost:%s/seriouslykill' % pms_global.port)
        else:
            pass
    t = threading.Timer(1.0, shutdown).start()
    #Timer(1.0, shutdown).start()  # wait 1 second
    return "Shutting down..."

###############################################################


if __name__ == '__main__':
    try:
        if len(sys.argv) > 1:
            pms_global.port = int(sys.argv[1])
            pms_global.host = sys.argv[2]
            pms_global.token = sys.argv[3]
            flag_test = False
        else:
            pms_global.port = 35400
            pms_global.host = '127.0.0.1:32400'
            pms_global.token = ''#'gpKwA5mBgHNLTpyrRaVe'
            flag_test = True
        
        send_start_noti(flag_test)
        logger.debug(sys.argv)
        logger.debug('SJVA IN PMS Start on port : %s', pms_global.port)
        if flag_test:
            print 'Please run by plugin!!'
        else:
            pms_global.app.run(host='0.0.0.0', port=pms_global.port, debug=False)
    except Exception, e:
        logger.debug('Exception:%s', e) 
        logger.debug(traceback.format_exc())

