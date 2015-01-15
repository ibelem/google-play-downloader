#! /usr/bin/env python
# -*- coding: utf-8 -*-

# http://www.lfd.uci.edu/~gohlke/pythonlibs/#pycurl
# C:\Python27\Scripts>pip --proxy http://proxy.cd.intel.com:911 install certifi

import sys, os
from datetime import *
import time
import config, comm
import downloader as dl

def preconfig():
  d = datetime.now()
  config.__starttime__ = d.strftime('%Y-%m-%d %H:%M:%S')
  t = config.__starttime__.replace(' ', '_').replace(':', '-')
  config.__logfile__ = os.path.join(config.__scriptpath__, 'result', 'play_dl_' + t + '.log')

def main():
    preconfig()
    #dl.url_connection('https://play.google.com')

    if(dl.url_connection('https://play.google.com')):
        dl.run_apk_list()

    #for i in dl.search_apk_list_by_keywords('欧朋'):
    #   dl.get_apk_info_by_package(i)
    #   dl.get_apk_url(i)

    #dl.get_apk_url('com.youdao.note')
    #dl.get_apk_url('com.funcity.taxi.passenger')

    for i in dl.get_apk_list():
        dl.get_apk_info_by_package(i)

if __name__ == '__main__':
    sys.exit(main())

# https://play.google.com/store/apps/details?id=fq.router2

