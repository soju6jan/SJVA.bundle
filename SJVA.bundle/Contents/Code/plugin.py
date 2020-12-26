# -*- coding: utf-8 -*-
import os
import io
import threading
import time
import zipfile
import urllib
import shutil
import re
import traceback
import subprocess
try:
    import base
except:
    pass

CURRENT_PATH = re.sub(r'^\\\\\?\\', '', os.getcwd())

class PluginHandle(object):
    plugin_list = None
    thread_instance = None

    @classmethod
    def get_list(cls):
        #url = 'https://raw.githubusercontent.com/soju6jan/SJVA.bundle/master/plugin_list.json'
        url = 'https://raw.githubusercontent.com/soju6jan/sjva_support/master/plex_install_plugin_list.json'
        data = JSON.ObjectFromURL(url)
        Log(data)
        cls.plugin_list = data
        return cls.plugin_list

    @classmethod
    def is_plugin_install(cls, identifier):
        if identifier.startswith('scanner_show'):
            plex_root = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_PATH)))
            scanner_path = os.path.join(plex_root, 'Scanners', 'Series', identifier.split('|')[1])
            try:
                return os.path.exists(scanner_path)
            except:
                return False
        else:
            data = JSON.ObjectFromURL('http://127.0.0.1:32400/:/plugins')
            Log(data)
            for plugin in data['MediaContainer']['Plugin']:
                if identifier == plugin['identifier']:
                    return True
        return False

    @classmethod
    def install(cls, identifier):
        if cls.thread_instance is not None:
            return 'RUNNING'
        data = None
        if cls.plugin_list is None:
            cls.get_list()
        for _ in cls.plugin_list['list']:
            if identifier == _['identifier']:
                data = _
                break
        Log('DATA %s', data)
        if data is None:
            return 'ERROR'
        cls.thread_instance = PluginInstallThread()
        cls.thread_instance.set_data(cls, data)
        cls.thread_instance.daemon = True
        cls.thread_instance.start()
        return 'OK'
    
    """
    @classmethod
    def update(cls):
        return cls.install('com.plexapp.plugins.SJVA')
    """
    
    @classmethod
    def update(cls):
        #copy
        import threading
        def thread_function():
            THIS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(base.CURRENT_PATH))), 'Plug-ins', 'SJVA.bundle', 'Contents', 'Code', 'plugin.py') 
            DEST_FILE = os.path.join(CURRENT_PATH, 'plugin.py') 
            try:
                shutil.copyfile(THIS_FILE, DEST_FILE)
                command = '"%s" "%s"' % (base.PYTHON, DEST_FILE)
                Log('UPDATE2 %s',  command )
                if base.is_windows():
                    #shell true 파일쓰기 권한 없음.
                    proc = subprocess.Popen(command)
                else:
                    #proc = subprocess.Popen(command, env={"PYTHONPATH": "."})
                    proc = subprocess.Popen(command, shell=True, env={"PYTHONIOENCODING":"utf-8", "PYTHONPATH": ".", "LANG":"en_US.UTF-8"})  
                    """
                    try:
                        aaa = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, env={"PYTHONIOENCODING":"utf-8", "PYTHONPATH": ".", "LANG":"en_US.UTF-8"})  
                    except subprocess.CalledProcessError as cpe:
                        Log('!!!!!!!!!!!!!!!!!!!! %s', cpe.output.decode('cp949'))
                        #Log('!!!!!!!!!!!!!!!!!!!! %s', cpe.output.decode('cp949')) #윈도우
                    """
                proc.communicate()
            except Exception, e: 
                Log('Exception:%s', e)
                Log(traceback.format_exc())
        t = threading.Thread(target=thread_function, args=())
        #t.daemon = True
        t.start() 
        return 'OK'

    @classmethod
    def get_git_version(cls):
        url = 'https://raw.githubusercontent.com/soju6jan/SJVA.bundle/master/SJVA.bundle/Contents/Code/version.py'
        data = HTTP.Request(url).content
        Log(data)
        return data

class PluginInstallThread(threading.Thread):
    data = None
    plugin_handle_instance = None

    def set_data(self, plugin_handle_instance, data):
        self.plugin_handle_instance = plugin_handle_instance
        self.data = data

    def run(self):
        try:
            if self.data['type'] == 'agent' or self.data['type'] == 'normal':
                zip_file_url = self.data['url_zip']
                try:
                    filedata = HTTP.Request(zip_file_url).content
                except:
                    try:
                        import urllib, urllib2
                        request = urllib2.Request(zip_file_url)
                        response = urllib2.urlopen(request)
                        filedata = response.read()
                    except:
                        pass
                temp_path = os.path.join(CURRENT_PATH, 'zip')
                try:
                    if not os.path.exists(temp_path):
                        os.mkdir(temp_path)
                    else:
                        shutil.rmtree(temp_path)
                        os.mkdir(temp_path)
                except:
                    pass
                zip_temp_filename = os.path.join(temp_path, self.data['identifier'] + '.zip')
                with io.open(zip_temp_filename, "wb") as local_file:
                    local_file.write(filedata)
                zip_instance = zipfile.ZipFile(zip_temp_filename)
                zip_instance.extractall(temp_path)
                zip_instance.close()
                os.remove(zip_temp_filename)
                
                listdir = os.listdir(temp_path)
                if len(listdir) == 1:
                    zip_root = listdir[0]
                    if 'manual' in self.data: 
                        for tmp1 in self.data['manual']:
                            if tmp1['type'] == 'move':
                                manual_src = temp_path
                                for tmp2 in tmp1['src']:
                                    manual_src = os.path.join(manual_src, tmp2)
                                manual_dest = temp_path
                                for tmp2 in tmp1['dest']:
                                    manual_dest = os.path.join(manual_dest, tmp2)
                                shutil.move(manual_src, manual_dest)
                            elif tmp1['type'] == 'move_all_file':
                                manual_dest = temp_path
                                for tmp2 in tmp1['dest']:
                                    manual_dest = os.path.join(manual_dest, tmp2)
                                manual_src = temp_path
                                for tmp2 in tmp1['src']:
                                    manual_src = os.path.join(manual_src, tmp2)
                                for tmp3 in os.listdir(manual_src):
                                    shutil.move(os.path.join(manual_src, tmp3), manual_dest)
                    if 'root' in self.data:
                        bundle = self.data['root'][len(self.data['root'])-1]
                        dest = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_PATH))), 'Plug-ins', bundle)
                        src = temp_path
                        for _ in self.data['root']:
                            src = os.path.join(src, _)
                    else:
                        dest = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_PATH))), 'Plug-ins', zip_root.replace('-master', '').replace('-main', ''))
                        src = os.path.join(temp_path, zip_root)
                    move_or_copy = 'move'
                    if self.data["identifier"] == "com.plexapp.plugins.SJVA":
                        move_or_copy = 'copy'
                        #dest = os.path.dirname(dest)
                    else:
                        if os.path.exists(dest):
                            try:
                                shutil.rmtree(dest)
                            except:
                                #dest = os.path.dirname(dest)
                                move_or_copy = 'copy'
                                pass
                    if move_or_copy == 'move':
                        shutil.move(src, dest) 
                    else:
                        if __name__ == '__main__':
                            import distutils.dir_util
                            distutils.dir_util.copy_tree(src, dest)
                        else:
                            shutil.copy(src, dest)
                    #shutil.rmtree(temp_path)
            elif self.data['type'] == 'scanner_show':
                plex_root = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_PATH)))
                series_dir = ['Scanners', 'Series']
                tmp = plex_root
                for _ in series_dir:
                    tmp = os.path.join(tmp, _)
                    if not os.path.exists(tmp):
                        os.mkdir(tmp)
                scanner_path = os.path.join(plex_root, 'Scanners', 'Series', self.data['identifier'].split('|')[1])
                if os.path.exists(scanner_path):
                    os.remove(scanner_path)
                filedata = HTTP.Request(self.data['url']).content
                with io.open(scanner_path, "wb") as local_file:
                    local_file.write(filedata)
        except Exception as e:
            try:
                Log('Exception : %s', e)
                Log(traceback.format_exc()) 
            except:
                print e
                print traceback.format_exc()

        finally:
            if self.plugin_handle_instance is not None:
                self.plugin_handle_instance.thread_instance = None
            try:
                #shutil.rmtree(temp_path)
                pass
            except:
                pass

# 지우지말것
if __name__ == '__main__':
    def Log(*arg, **args):
        print arg
        print args
    #with io.open('test', "w") as local_file:
    #    local_file.write(u'test')
    data = {}
    data['type'] = "normal"
    data["identifier"] = "com.plexapp.plugins.SJVA"
    data["name"] = "SJVA"
    data["url_icon"] = "https://github.com/soju6jan/SJVA.bundle/raw/master/SJVA.bundle/Contents/Resources/icon-default.png"
    data["description"] = "SJVA"
    data["author"] = "soju6jan"
    data["url_zip"] = "https://github.com/soju6jan/SJVA.bundle/archive/master.zip"
    data["root"] = ["SJVA.bundle-master", "SJVA.bundle"]

    thread_instance = PluginInstallThread()
    thread_instance.set_data(None, data)
    thread_instance.daemon = False
    thread_instance.start()
    thread_instance.join()
