#!/usr/bin/env python
# -*- coding: utf-8 -*-
_author__ = 'lvxinwei'
import json
from QQCore import *
import redis,time
class MsgHandle:
    def __init__(self):
        self.qq=QQCore(True)
        self.qq.getFriendInfo()
        self.redis=redis.StrictRedis(host='lvxinwei.com', port=6379, db=0)
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
    def start(self):
        msg_in=self.__lpop('message_box_in1')
        msg_out=self.__lpop('message_box_out')
        self.handleMsgIn(msg_in)
        print msg_out
        self.handleMsgOut(msg_out)
    def handleMsgOut(self,msg):
        if not msg:
            return
        msg=json.loads(msg)
        account=msg['account']
        time=msg['time']
        content=msg['content']
        uin=self.qq.friendList[account]
        if self.qq.replay(uin,account):
            return True
        else :
            print 'replay error'
    def handleMsgIn(self,msg):
        if not msg:
            return
        json.loads(msg)
        poll_type=msg['poll_type']
        if poll_type=='message':
            ret=self.__handleMessage(msg)
            self.__setValue(ret[0],ret[1])
        if poll_type=='kick_message':
            ret=self.__kickMessage(msg)
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
    def __handleMessage(self,msg):
        poll_type=msg['poll_type']
        time=str(msg['value']['time'])
        account=self.qq.getAccountByUin(msg['value']['from_uin'])
        if not account:
            account=msg['value']['from_uin']
        msg_id=msg['value']['msg_id']
        content=self.__combineMsg(msg['value']['content'])
        key=poll_type+":"+str(account)+":"+str(time)+":"+str(msg_id)+":in"
        return [key,content]
    def __kickMessage(self,msg):
        key=msg['poll_type']
        key=key+":"+str(int(time.time()))
        return [key,msg['value']['reason']]

if __name__=='__main__':
    msgh=MsgHandle()
    msgh.start()
