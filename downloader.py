#! /usr/bin/env python
# -*- coding: utf-8 -*-

# http://www.lfd.uci.edu/~gohlke/pythonlibs/#pycurl
# C:\Python27\Scripts>pip --proxy http://proxy.cd.intel.com:911 install certifi

import sys, os
import StringIO, zlib, re
import logging
import pycurl, certifi
import config, comm

email = config.__email__
passwd = config.__passwd__
deviceid = config.__device_id__
devicename = config.__device_name__
country = config.__country__
operator = config.__operator__
sdklevel = config.__sdklevel__
scriptpath = config.__scriptpath__
apkdllist = config.__apkdllist__
apkdllistpath = os.path.join(scriptpath, apkdllist)
proxy = {
  'url': config.__proxyurl__,
  'port': config.__proxyport__,
  'type': config.__proxytype__
}

operatorlist = {'USA': {'AT&T': '31038', 'Sprint': '31002', 'T-Mobile': '31020'},}
googletoken = ''
request = ''

try:
    # python 3
    from urllib.parse import urlencode
except ImportError:
    # python 2
    from urllib import urlencode

def curl_request(url, method, ua, header, postdata, cookie):
  c = pycurl.Curl()

  b = StringIO.StringIO()
  c.setopt(c.WRITEFUNCTION, b.write)

  c.setopt(c.URL, url)
  c.setopt(c.SSL_VERIFYPEER, 0)
  c.setopt(c.SSL_VERIFYHOST, 0)
  c.setopt(c.CAINFO, certifi.where())
  c.setopt(c.FOLLOWLOCATION, 1)
  c.setopt(c.CONNECTTIMEOUT, 60)
  c.setopt(c.TIMEOUT, 300)
  c.setopt(c.USERAGENT, ua)
  c.setopt(c.HTTPHEADER, header)

  if cookie:
      c.setopt(c.COOKIE, cookie)

  if method == 'POST':
    postfields = urlencode(postdata)
    c.setopt(c.POSTFIELDS, postfields)

  if(proxy['url']):
    c.setopt(c.PROXY, proxy['url'])
    c.setopt(c.PROXYPORT, int(proxy['port']))
    proxytype = ''
    if proxy['type'] == 'socks5':
      proxytype = c.PROXYTYPE_SOCKS5
    elif proxy['type'] == 'socks4':
      proxytype = c.PROXYTYPE_SOCKS4
    elif proxy['type'] == 'https' or proxy['type'] == 'https':
      proxytype = c.PROXYTYPE_HTTP
    c.setopt(c.PROXYTYPE, proxytype)

    c.perform()
    httpresponse = b.getvalue()
    httpcode = c.getinfo(c.HTTP_CODE)
    c.close()
    return (httpcode, httpresponse)


def download_apk(packagename):
  fun = 'download_apk'
  l(fun, 'Downloading '+ packagename +' from Google Play...')
  apk_url = get_apk_url(packagename)
  real_url = apk_url.split('#')[0]
  cookies = 'MarketDA='+ apk_url.split('#')[1]

  try:

    ua = 'AndroidDownloadManager/4.4.2 (Linux; U; Android 4.4.2; Galaxy Nexus Build/JRO03E)'
    header = ['Accept-Encoding:']
    x, y = curl_request(real_url, 'GET', ua, header, {}, cookies)

    print str(x)
    packageapk = packagename + '.apk'
    packagepath = os.path.join(scriptpath, 'apk', packageapk)
    with open(packagepath,'wb') as op:
      op.write(y)
    validate_apk(packageapk)
    l(fun, 'Downloaded '+ packagename +' from Google Play')
    l(fun, '-----------------------------------------------------------------------------------')
  except Exception, ex:
    l(fun, str(ex))
    l(fun, 'Download '+ packagename +' from Google Play ----- FAIL')
    l(fun, '-----------------------------------------------------------------------------------')

def validate_apk(packageapk):
    fun = 'validate_apk'
    l(fun, 'APK validating: ' + packageapk)
    packagepath = os.path.join(scriptpath, 'apk', packageapk)
    try:
      aaptpath = os.path.join(scriptpath, 'platform-tools', 'aapt.exe')
      aapt_cmd = aaptpath + ' d badging ' + packagepath
      content = os.popen(aapt_cmd).read()
      if content.find('ERROR') == -1:
          info = content.split("'")
          if len(info) > 5:
              version_postfix = info[5]
              packagepath = packagepath.replace('_' + version_postfix, '')
              packagepath_version = packagepath.replace('.apk','') + '_' + version_postfix + '.apk'
              if os.path.exists(packagepath_version):
                  os.remove(packagepath)
                  l(fun, packagepath_version + ' exists.')
              else:
                  os.rename(packagepath, packagepath_version)
                  l(fun, 'Validated and saved APK as ' + packagepath_version)
              return packagepath_version
      else:
        l(fun, 'Validate '+ packageapk +' ----- FAIL')
    except Exception, ex:
      l(fun, str(ex))
      l(fun, 'Validate '+ packageapk +' ----- FAIL')

def get_apk_url(packagename):
  fun = 'get_apk_url'
  l(fun, 'Fecthing APK URL ['+ packagename +']:')
  request = generate_request(packagename)
  if len(request):
    url = 'https://android.clients.google.com/market/api/ApiRequest'
    ua = 'Android-Finsky/3.7.13 (api=3,versionCode=8013013,sdk=16,device=crespo,hardware=herring,product=soju)'

    header = ['Content-Type: application/x-www-form-urlencoded',
                           'Accept-Language: en_US',
                           'Authorization: GoogleLogin auth=%s' %googletoken,
      'X-DFE-Enabled-Experiments: cl:billing.select_add_instrument_by_default',
      'X-DFE-Unsupported-Experiments: nocache:billing.use_charging_poller,market_emails,buyer_currency,prod_baseline,checkin.set_asset_paid_app_field,shekel_test,content_ratings,buyer_currency_in_app,nocache:encrypted_apk,recent_changes',
      'X-DFE-Device-Id: %s' %deviceid,
      'X-DFE-Client-Id: am-android-google',
      'X-DFE-SmallestScreenWidthDp: 480',
      'X-DFE-Filter-Level: 3',
      'Accept-Encoding: ',
      'Host: android.clients.google.com']

    postdata = {
      'version': 2,
      'request': request
    }

    try:
      x, y = curl_request(url, 'POST', ua, header, postdata, '')

      if x == 429:
        raise Exception('Too many request')
      elif x == 403:
          raise Exception('Forbidden')
      elif x == 401:
          raise Exception('Unauthorized')
      elif x != 200:
          l(fun, str(x))
          raise Exception('Unexpected HTTP Status Code')
      gzipped_content = y
      response = zlib.decompress(gzipped_content, 16 + zlib.MAX_WBITS)
      dl_url = ''
      dl_cookie = ''

      match = re.search('(https?:\/\/[^:]+)', response)
      if match is None:
          l(fun, response)
          raise Exception('Unexpected https response' + 'for [' +packagename +']')
      else:
          dl_url = match.group(1)
          l(fun, 'Got APK URL ['+ packagename +']: ' + dl_url)

      match = re.search('MarketDA.*?(\d+)', response)
      if match is None:
          raise Exception('Get cookie failed')
      else:
          dl_cookie = match.group(1)
          l(fun, 'Got URL Cookie: ' + dl_cookie)
      return dl_url + '#' + dl_cookie
    except Exception, ex:
      l(fun, str(ex))
      l(fun, 'APK URL ['+ packagename +'] Not Found ---- FAIL')


def generate_request(packagename):
  fun = 'generate_request'

  try:
    l(fun, 'Generating requests:')
    googletoken = get_google_token()
    if len(googletoken):
      para = [googletoken, True, sdklevel, deviceid,
                      devicename, 'en', 'us', operator, operator,
                      operatorlist[country][operator], operatorlist[country][operator],
                      packagename, packagename]
      request = comm.generate_request(para)
      if request:
        l(fun, 'Generated requests')
        return request
      else:
        return False
    else:
      l(fun, 'Generate requests ----- FAIL')
  except Exception, ex:
      l(fun, str(ex))
      l(fun, 'Generate requests ----- FAIL')

def get_google_token():
  fun = 'get_google_token'

  try:
    l(fun, 'Getting account token:')

    url = 'https://www.google.com/accounts/ClientLogin'
    ua = 'AndroidDownloadManager/4.4.2 (Linux; U; Android 4.4.2; Galaxy Nexus Build/JRO03E)'
    header = ['Content-Type: application/x-www-form-urlencoded']
    postdata = {
        'Email': email,
        'Passwd': passwd,
        'service': 'androidsecure',
        'accountType': 'HOSTED_OR_GOOGLE'
    }
    x, y = curl_request(url, 'POST', ua, header, postdata, '')

    html = y.split('\n')
    if html[0] == 'Error=BadAuthentication':
        l(fun, 'Error=BadAuthentication ----- FAIL')
        sys.exit(0)
    auth = [i for i in html if i.find('Auth=') != -1]
    if auth:
        account_token = auth[0].split('=')[1]
        if account_token != None:
            l(fun, 'Google account token fetched, aloha')
            return account_token
        else:
            l(fun, 'Get token failed')
            raise Exception('Get token failed')
  except Exception, ex:
    l(fun, str(ex))
    l(fun, 'Get account token ----- FAIL')

def url_connection(url):
  fun = 'connect_url'
  try:
    l(fun, 'Connecting ' + url)
    ua = 'AndroidDownloadManager/4.4.2 (Linux; U; Android 4.4.2; Galaxy Nexus Build/JRO03E)'
    x, y = curl_request(url, 'GET', ua, [], {}, '')
  except Exception, ex:
    l(fun, str(ex) + ' Connect to ' + url + ' ----- FAIL')
    return False
  else:
    if x == 200:
      l(fun, 'Connected to ' + url)
      return True
    else:
      l(fun, url + ' ' + str(x))
      raise Exception('Unexpected HTTP Status Code')

def l(fun, content):
  comm.log_msg(config.__logfile__, fun, content)

def run_apk_list():
    fun = 'apk_list'
    apklist = []
    for g in open(apkdllistpath, 'r'):
        apklist.append(g.strip())
    if apklist:
        for i in apklist:
            download_apk(i)
    else:
       l(fun, 'No Android packages added in ' + apkdllistpath)
       sys.exit(0)


# https://play.google.com/store/apps/details?id=fq.router2

