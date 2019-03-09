# -*- coding: utf-8 -*-
import os
import sys
import traceback
import sqlite3
import pms_global


logger = pms_global.logger_init(os.path.splitext(os.path.basename(__file__))[0])

class PLEX_DB(object):
    section_list = None

    @classmethod
    def init(cls):
        cls.section_list = cls.get_section_list()
       
    @classmethod
    def get_section_list(cls):
        try:
            conn = sqlite3.connect(pms_global.DB_FILE)
            cur = conn.cursor()
            sql = "SELECT library_section_id, root_path FROM section_locations"
            cur.execute(sql)
            rows = cur.fetchall()
            ret = []
            for row in rows:
                ret.append([row[0], row[1]])
            conn.close()
            return ret
        except Exception, e:
            logger.debug('Exception:%s', e)
            logger.debug(traceback.format_exc())

    @classmethod
    def get_section_id(cls, filename):
        #Movie Movie4K 
        max_section_name = ''
        max_section_id = ''
        try:
            #M:\MovieETC\무자막\
            for section in cls.section_list:
                if filename.find(section[1]) != -1:
                    if len(max_section_name) < len(section[1]):
                        max_section_name = section[1]
                        max_section_id = section[0]
                    #return int(section[0])
            if max_section_id != '':
                return int(max_section_id)
            else:
                return -1
        except Exception, e:
            logger.debug('Exception:%s', e)
            logger.debug(traceback.format_exc())

    @classmethod
    def is_exist_in_library(cls, filename):
        try:
            conn = sqlite3.connect(pms_global.DB_FILE)
            cur = conn.cursor()
            sql = "SELECT * FROM media_parts WHERE file = '%s'" % filename
            #cur.execute(sql, (filename))
            cur.execute(sql)
            rows = cur.fetchall()
            if len(rows) > 0:
                ret = True
            else:
                ret = False
            conn.close()
            return ret
        except Exception, e:
            logger.debug('Exception:%s', e)
            logger.debug(traceback.format_exc())


if __name__ == '__main__':
    import os
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')
    #DBManager.insert_download_korea_tv()
