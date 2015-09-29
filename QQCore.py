#!/usr/bin/env python
# -*- coding: utf-8 -*-
_author__ = 'lvxinwei'
import json,time
import random
import datetime
import re
import os
import pickle
import redis
from HttpRequests import *
def get_revalue(html, rex, er, ex):
    v = re.search(rex, html)
    if v is None:
        if ex:
            raise TypeError(er)
        else:
            pass
        return ''
    return v.group(1)


def date_to_millis(d):
    return int(time.mktime(d.timetuple())) * 1000
class QQCore:
    def __init__(self,isLoadData=False):
        self.dataFileName="data.txt"
        self.req = HttpRequests(isLoadData);
        self.data={}
        self.data['client_id']= int(random.uniform(111111, 888888))
        self.data['ptwebqq'] = ''
        self.data['psessionid'] = ''
        self.data['selfuin']=''
        self.appid = 0
        self.data['vfwebqq'] = ''
        self.qrcode_path = "./vcode.jpg"  # QRCode保存路径
        self.username = ''
        self.account = 0
        self.friendList={}
        self.uinInfo={}
        self.redis=redis.StrictRedis(host='localhost', port=6379, db=0)
        if isLoadData:
            self.data=self.__loadData()
        pass
    #获取相关信息
    def __loadData(self):
        with open(self.dataFileName, 'r') as f:
            data=pickle.load(f)
        f.close()
        return  data
    #保存data
    def __saveData(self):
        with open(self.dataFileName, 'w') as f:
             pickle.dump(self.data,f)
        f.close()
    #计算hash信息
    def __hash(self,selfuin,ptwebqq):
        selfuin=str(selfuin)
        selfuin += ""
        N=[0,0,0,0]
        for T in range(len(ptwebqq)):
            N[T%4]=N[T%4]^ord(ptwebqq[T])
        U=["EC","OK"]
        V=[0, 0, 0, 0]
        V[0]=int(selfuin) >> 24 & 255 ^ ord(U[0][0])
        V[1]=int(selfuin) >> 16 & 255 ^ ord(U[0][1])
        V[2]=int(selfuin) >>  8 & 255 ^ ord(U[1][0])
        V[3]=int(selfuin)       & 255 ^ ord(U[1][1])
        U=[0,0,0,0,0,0,0,0]
        U[0]=N[0]
        U[1]=V[0]
        U[2]=N[1]
        U[3]=V[1]
        U[4]=N[2]
        U[5]=V[2]
        U[6]=N[3]
        U[7]=V[3]
        N=["0","1","2","3","4","5","6","7","8","9","A","B","C","D","E","F"]
        V=""
        for T in range(len(U)):
            V+= N[ U[T]>>4 & 15]
            V+= N[ U[T]    & 15]
        return V
    def login_by_qrcode(self):
        initurl_html = self.req.get('http://w.qq.com/login.html')
        initurl = get_revalue(initurl_html, r'\.src = "(.+?)"', "Get Login Url Error.", 1)
        html = self.req.get(initurl + '0')
        appid = get_revalue(html, r'var g_appid =encodeURIComponent\("(\d+)"\);', 'Get AppId Error', 1)
        sign = get_revalue(html, r'var g_login_sig=encodeURIComponent\("(.*?)"\);', 'Get Login Sign Error', 0)
        js_ver = get_revalue(html, r'var g_pt_version=encodeURIComponent\("(\d+)"\);', 'Get g_pt_version Error', 1)
        mibao_css = get_revalue(html, r'var g_mibao_css=encodeURIComponent\("(.+?)"\);', 'Get g_mibao_css Error', 1)
        star_time = date_to_millis(datetime.datetime.utcnow())
        error_times = 0
        ret = []
        while True:
            error_times += 1
            vcodeUrl='https://ssl.ptlogin2.qq.com/ptqrshow?appid={0}&e=0&l=L&s=8&d=72&v=4'.format(appid)
            self.req.downloadFile(vcodeUrl,self.qrcode_path)
            print "Please scan the downloaded QRCode"
            while True:
                checkLoginUrl='https://ssl.ptlogin2.qq.com/ptqrlogin?webqq_type=10&remember_uin=1&login2qq=1&aid={0}&u1=http%3A%2F%2Fw.qq.com%2Fproxy.html%3Flogin2qq%3D1%26webqq_type%3D10&ptredirect=0&ptlang=2052&daid=164&from_ui=1&pttype=1&dumy=&fp=loginerroralert&action=0-0-{1}&mibao_css={2}&t=undefined&g=1&js_type=0&js_ver={3}&login_sig={4}'.format(
                        appid, date_to_millis(datetime.datetime.utcnow()) - star_time, mibao_css, js_ver, sign);
                html = self.req.get(checkLoginUrl,{'Referer':initurl})
                ret = html.split("'")
                time.sleep(2)
                if ret[1] in ('0', '65'):  # 65: QRCode 失效, 0: 验证成功, 66: 未失效, 67: 验证中
                    break
            if ret[1] == '0' or error_times > 10:
                break
        if ret[1] != '0':
            return
        print "QRCode scaned, now logging in."
        # 删除QRCode文件
        if os.path.exists(self.qrcode_path):
            os.remove(self.qrcode_path)
        # 记录登陆账号的昵称
        self.username = ret[11]
        url = get_revalue(self.req.get(ret[5]), r' src="(.+?)"', 'Get mibao_res Url Error.', 0)
        if url != '':
            html = self.req.get(url.replace('&amp;', '&'))
            url = get_revalue(html, r'location\.href="(.+?)"', 'Get Redirect Url Error', 1)
            self.req.get(url)
        self.data['ptwebqq'] = self.req.getCookies()['ptwebqq']
        login_error = 1
        ret = {}
        while login_error > 0:
            try:
                html = self.req.post('http://d.web2.qq.com/channel/login2', {
                    'r': '{{"ptwebqq":"{0}","clientid":{1},"psessionid":"{2}","status":"online"}}'.format(self.data['ptwebqq'] ,
                                                                                                          self.data['client_id'] ,
                                                                                                          self.data['psessionid'] )
                }, {'Referer':"http://d.web2.qq.com/proxy.html?v=20030916001&callback=1&id=2"} )
                ret = json.loads(html)
                login_error = 0
            except:
                login_error += 1
                print "login fail, retrying..."
                exit()

        if ret['retcode'] != 0:
            print ret
            return
        self.data['vfwebqq']  = ret['result']['vfwebqq']
        self.data['psessionid']  = ret['result']['psessionid']
        self.data['selfuin'] = ret['result']['uin']
        self.__saveData()
    def relogin(self, error_times=0):
        if error_times >= 10:
            return False
        try:
            html = self.req.post('http://d.web2.qq.com/channel/login2', {
                'r': '{{"ptwebqq":"{0}","clientid":{1},"psessionid":"{2}","key":"","status":"online"}}'.format(
                    self.req.getCookies()['ptwebqq'],
                    self.data['client_id'] ,
                    self.data['psessionid'] )
            } )
            ret = json.loads(html)
            self.data['vfwebqq']  = ret['result']['vfwebqq']
            self.data['psessionid']  = ret['result']['psessionid']
            return True
        except:
            return self.relogin(error_times + 1)
    #处理消息
    def __handleMsg(self,msgs):
        print msgs
        for msg in msgs:
            temp=json.dumps(msg)
            self.redis.rpush("message_box_in",temp)


    def getAccountByUin(self,uin):
        if uin in self.uinInfo:
            return self.uinInfo[uin]
        else:
            ret=self.uin_to_account(uin)
            if ret:
                return ret
        return False

    #获取好友详细信息
    def getFriendInfo(self):
        ret=self.getFriendList()
        if not ret:
            return False
        friendlist={}
        uinInfo={}
        for user in ret['marknames']:
            if user['uin'] not in friendlist:
                friendlist[user['uin']]={}
            friendlist[user['uin']]['markname']=user['markname']
        for user in ret['info']:
             if user['uin'] not in friendlist:
                friendlist[user['uin']]={}
             friendlist[user['uin']]['nick']=user['nick']
             friendlist[user['uin']]['uin']=user['uin']
             account=self.uin_to_account(user['uin'])
             friendlist[user['uin']]['account']=account
             friendlist[account]=friendlist[user['uin']]
             del friendlist[user['uin']]
             uinInfo[user['uin']]=account
        self.friendList=friendlist
        self.uinInfo=uinInfo
        return friendlist

    #获取所有用户列表，但是不含QQ号
    def getFriendList(self):
        try :
            requestUrl="http://s.web2.qq.com/api/get_user_friends2"
            hash=self.__hash(self.data['selfuin'],self.req.getCookies()['ptwebqq'])
            ret=self.req.post(requestUrl,{'vfwebqq':self.data['vfwebqq'],'hash':hash})
            ret=json.loads(ret)
            if ret['retcode'] ==0:
                return ret['result']
            else :
                return False
        except Exception,e:
            print e
    #通过UIN获取QQ号
    def uin_to_account(self, uin):
        uin_str = str(uin)
        try:
            info = json.loads(self.req.get(
                'http://s.web2.qq.com/api/get_friend_uin2?tuin={0}&type=1&vfwebqq={1}'.format(uin_str, self.data['vfwebqq'] )))
            if info['retcode'] != 0:
                raise TypeError('uin to account result error')
            info = info['result']
            return info['account']
        except Exception ,e:
            print e
            pass
    #回复私人信息
    def reply(self,tuin,reply_content,message_id=78652,error_times=0):
        if error_times>4:
            return False
        fix_content = reply_content.replace("\\", "\\\\\\\\").replace("\n", "\\\\n").replace("\t", "\\\\t").encode("utf-8")
        rsp = ""

        req_url = "http://d.web2.qq.com/channel/send_buddy_msg2"
        data = (
            ('r', '{{"to":{0}, "face":594, "content":"[\\"{4}\\", [\\"font\\", {{\\"name\\":\\"Arial\\", \\"size\\":\\"10\\", \\"style\\":[0, 0, 0], \\"color\\":\\"000000\\"}}]]", "clientid":"{1}", "msg_id":{2}, "psessionid":"{3}"}}'.format(tuin, self.data['client_id'], message_id,self.data['psessionid'], fix_content)),
            ('clientid', self.data['client_id']),
            ('psessionid', self.data['psessionid'])
        )
        ret=self.req.post(req_url,data)
        ret=json.loads(ret)
        if ret['retcode']==0:
            return True
        else:
            return self.reply(tuin,reply_content,message_id,error_times+1)
    def check_msg(self):
        # 调用后进入单次轮询，等待服务器发回状态。
        ret = self.req.post('http://d.web2.qq.com/channel/poll2', {
            'r': '{{"ptwebqq":"{1}","clientid":{2},"psessionid":"{0}","key":""}}'.format(self.data['psessionid'], self.data['ptwebqq'],self.data['client_id'])
        })
        try:
            if ret == "":
                return self.check_msg()
            ret = json.loads(ret)
            ret_code = ret['retcode']
            if ret_code ==0:
                self.__handleMsg(ret['result'])
                return
            if ret_code in (102,):
                print 'no message'
                time.sleep(1)
                return
            if ret_code in (103,):
                time.sleep(1)
                return self.check_msg()

            if ret_code in (121,):
                return self.check_msg(5)
            elif ret_code == 100006:
                print 'post data error'
                return
            elif ret_code == 116:
                self.data['ptwebqq'] = ret['p']
                self.__saveData()
                return
            else:

                return

        except Exception,e:
            print e
            pass









