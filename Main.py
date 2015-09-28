#!/usr/bin/env python
# -*- coding: utf-8 -*-
_author__ = 'lvxinwei'
from QQCore import *
qq=QQCore(False)
qq.login_by_qrcode()
while True:
    qq.check_msg()
    time.sleep(2)
