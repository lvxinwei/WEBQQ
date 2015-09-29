#!/usr/bin/env python
# -*- coding: utf-8 -*-
_author__ = 'lvxinwei'
import json
from QQCore import *
import redis,time
def sortMsg(a,b):
    a=":".join(a.split(":")[0:-1])
    b=":".join(b.split(":")[0:-1])
    return cmp(a,b)
class MsgHandle:
    def __init__(self):
        self.qq=QQCore(True)
        self.qq.getFriendInfo()
        self.redis=redis.StrictRedis(host='127.0.0.1', port=6379, db=0)
        pass
    def __getValue(self,key):
        return self.redis.get(key)
    def __setValue(self,key,value):
        return self.redis.set(key,value)
    def __lpush(self,key,name):
        return self.redis.lpush(key,name)
    def __lpop(self,key):
        return self.redis.lpop(key)
    def __rpush(self,key,name):
        return self.redis.rpush(key,name)
    def __rpop(self,key):
        return self.redis.rpop(key)
    def __lrange(self,key,start=0,stop=-1):
        return self.redis.lrange(key,start,stop)
    def __getLikeKeys(self,key):
        return self.redis.keys(key)
    def getMsgByAccount(self,account):
        likeKey='message:'+str(account)+"*"
        keys=self.__getLikeKeys(likeKey)
        #对keys排序
        keys=sorted(keys,sortMsg)
        ret=[]
        for key in keys:
            ret.append([key,self.__getValue(key)])
        return ret
    def getLastMsgId(self,account):
        lastMsgKey=self.getMsgByAccount(account)[-1][0]
        return int(lastMsgKey.split(":")[-2])
    def start(self):
        msg_in=self.__lpop('message_box_in')
        msg_out=self.__lpop('message_box_out')
        self.handleMsgIn(msg_in)
        self.handleMsgOut(msg_out)
    def handleMsgOut(self,msg):
        if not msg:
            return
        msg=json.loads(msg)
        account=msg['account']
        msg_id=self.getLastMsgId(account)+1
        print msg_id
        time=msg['time']
        content=msg['content']
        uin=self.qq.friendList[account]['uin']
        if self.qq.reply(uin,content,msg_id):
            key="message:"+str(account)+":"+time+":"+str(msg_id)+":out"
            self.__setValue(key,content)
            return True
        else :
            print 'replay error'
    def handleMsgIn(self,msg):
        if not msg:
            return
        msg=json.loads(msg)
        poll_type=msg['poll_type']
        if poll_type=='message':
            ret=self.__handleNormalMessage(msg)
            self.__setValue(ret[0],ret[1])
        if poll_type=='kick_message':
            ret=self.__handleKickMessage(msg)
            self.__setValue(ret[0],ret[1])
    def __combineMsg(self,content):
        msgtxt = ""
        for part in content:
            if type(part) == type(u'\u0000'):
                msgtxt += part
            elif len(part) > 1:
                # 如果是图片
                if str(part[0]) == "offpic":
                    msgtxt += "[图片]"
                elif str(part[0]) == "cface":
                    msgtxt += "[表情]"
        return msgtxt
    def __handleNormalMessage(self,msg):
        poll_type=msg['poll_type']
        time=str(msg['value']['time'])
        account=self.qq.getAccountByUin(msg['value']['from_uin'])
        if not account:
            account=msg['value']['from_uin']
        msg_id=msg['value']['msg_id']
        content=self.__combineMsg(msg['value']['content'])
        key=poll_type+":"+str(account)+":"+str(time)+":"+str(msg_id)+":in"
        return [key,content]
    def __handleKickMessage(self,msg):
        key=msg['poll_type']
        key=key+":"+str(int(time.time()))
        return [key,msg['value']['reason']]

if __name__=='__main__':
    msgh=MsgHandle()
    while True:
        msgh.start()
        time.sleep(1)
    # print msgh.getLastMsgId(857280627)
    # print msgh.getMsgByAccount(857280627)
