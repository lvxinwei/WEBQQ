# -*- coding: utf-8 -*-
import requests
import pickle
from cookielib import LWPCookieJar
class HttpRequests:
    def __init__(self,isLoadCookie=False):
        self.req=requests.session()
        self.cookieFileName="cookieJar"
        if isLoadCookie :
            self.__loadCookie()
        self.req.headers['referer']='http://d.web2.qq.com/proxy.html?v=20030916001&callback=1&id=2'
        self.req.headers['Accept']= 'application/javascript, */*;q=0.8';
        self.req.headers['User-Agent']="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.125 Safari/537.36";
    def __addHeaders(self,headers):
        for k in headers:
            self.req.headers[k]=headers[k]
            pass
    def __saveCookies(self):
        with open(self.cookieFileName, 'w') as f:
             pickle.dump(requests.utils.dict_from_cookiejar(self.req.cookies), f)
    def __loadCookie(self):
        with open(self.cookieFileName) as f:
            cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
            self.req.cookies=cookies
    def get(self,url,headers=None):
        if headers:
            self.__addHeaders(headers)
        ret=self.req.get(url).text
        self.__saveCookies()
        return ret
    def post(self,url,data,headers=None,getCookie=None):
        if headers:
            self.__addHeaders(headers)
        ret=self.req.post(url,data=data).text
        self.__saveCookies()
        return ret
        pass
    def getCookies(self):
        return self.req.cookies
    def downloadFile(self,url,fileName):
        output = open(fileName, 'wb')
        output.write(self.req.get(url).content)
        output.close()




