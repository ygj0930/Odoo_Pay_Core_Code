# -*- coding:utf-8 -*-
#author：叶国坚


import socket
import string
import time
import random
import requests
import string
from xml.dom import minidom as dom
import json
import hashlib
import xmltodict
import sys
import urllib
import urllib2
import re

class WeixinMicroPayUtil(object):
    #====支付相关配置信息=======
    _APP_ID = "";  # 公众账号appid
    _MCH_ID = "";  # 商户号
    _API_KEY = "";  # key设置路径：微信商户平台(pay.weixin.qq.com) -->账户设置 -->API安全 -->密钥设置

    # 有关url
    _host_name = socket.gethostname()
    _ip_address = socket.gethostbyname(_host_name)
    _CREATE_IP = _ip_address;  # 发起支付ip
    _MICROPAY_URL = "https://api.mch.weixin.qq.com/pay/micropay"; #条码支付api
    _QUERY_URL = "https://api.mch.weixin.qq.com/pay/orderquery"; #查询订单支付结果api

    def do_weixinMicroPay(self,orderid,goodsName,goodsPrice,authCode,**kwargs):
        '''
        条码支付
        '''
        appid = self._APP_ID
        mch_id = self._MCH_ID
        key = self._API_KEY
        nonce_str = str(int(round(time.time() * 1000))) + str(random.randint(1, 999)) + string.join(random.sample(
            ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
             'v', 'w', 'x', 'y', 'z'], 5)).replace(" ", "")
        spbill_create_ip = self._CREATE_IP
        
        #构建参数
        params = {}
        params['appid'] = appid
        params['mch_id'] = mch_id
        params['nonce_str'] = nonce_str
        params['out_trade_no'] = orderid.encode('utf-8')  # 客户端生成并传过来，参数必须用utf8编码，否则报错
        params['total_fee'] = int(goodsPrice * 100)  # 单位是分，必须是整数
        params['spbill_create_ip'] = spbill_create_ip
        params['body'] = goodsName.encode('utf-8')  # 中文必须用utf-8编码，否则xml格式错误
        params['auth_code'] = authCode

        #构造参数字符串
        doc = dom.Document()
        self.get_xml_data(doc, params)
        sign = self.get_sign_for_wx(params, self._API_KEY)
        params['sign'] = sign
        signnode = doc.createElement('sign')
        signvalue = doc.createTextNode(sign)
        signnode.appendChild(signvalue)
        doc.getElementsByTagName('xml')[0].appendChild(signnode)

        # 向微信条码支付发出请求
        req = urllib2.Request(self._MICROPAY_URL)
        req.headers['Content-Type'] = 'text/xml'
        req.data = doc.toprettyxml()
        res_data = urllib2.urlopen(req)

        # 提取支付结果
        res_read = res_data.read()
        doc = xmltodict.parse(res_read)
        return_code = doc['xml']['return_code']

        # 此字段是通信标识，非交易标识，交易是否成功需要查看result_code来判断
        if return_code == 'SUCCESS': #说明订单提交成功
            return True
        else:
            return False

    def do_weixinMicroPay_query(self,orderid):
        '''
        条码支付结果查询
        '''
        appid = self._APP_ID
        mch_id = self._MCH_ID
        key = self._API_KEY
        out_trade_no = orderid.encode('utf-8')  # 客户端生成并传过来，参数必须用utf8编码，否则报错
        nonce_str = str(int(round(time.time() * 1000))) + str(random.randint(1, 999)) + string.join(random.sample(
            ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
             'v', 'w', 'x', 'y', 'z'], 5)).replace(" ", "")

        params = {}
        params['appid'] = appid
        params['mch_id'] = mch_id
        params['nonce_str'] = nonce_str
        params['out_trade_no'] = out_trade_no

        doc = dom.Document()
        self.get_xml_data(doc, params)
        sign = self.get_sign_for_wx(params, self._API_KEY)
        params['sign'] = sign
        signnode = doc.createElement('sign')
        signvalue = doc.createTextNode(sign)
        signnode.appendChild(signvalue)
        doc.getElementsByTagName('xml')[0].appendChild(signnode)

        # 发出查询请求
        req = urllib2.Request(self._QUERY_URL)
        req.headers['Content-Type'] = 'text/xml'
        req.data = doc.toprettyxml()
        res_data = urllib2.urlopen(req)

        # 提取支付结果
        res_read = res_data.read()
        doc = xmltodict.parse(res_read)

        #根据结果不同，返回数据
        return_code = doc['xml']['return_code']
        if return_code == 'SUCCESS':
            result_code = doc['xml']['result_code']
            # 业务结果
            if result_code == 'SUCCESS':
                trade_state = doc['xml']['trade_state']
                #支付成功
                if trade_state == 'SUCCESS':
                    buyer = doc['xml']['openid']
                    return (True, 'SUCCESS', u'支付成功 ',buyer)
                #未支付、支付中，则继续轮询
                elif trade_state == 'NOTPAY':
                    return (False, 'NOTPAY', u'未支付','')
                elif trade_state == 'USERPAYING':
                    return (False, 'USERPAYING', u'支付中','')
                #支付关闭、撤销、失败，则支付失败
                elif trade_state == 'CLOSED':
                    return (False, 'CLOSED', u'支付关闭','')
                elif trade_state == 'REVOKED':
                    return (False, 'REVOKED', u'支付撤销','')
                elif trade_state == 'PAYERROR':
                    return (False, 'PAYERROR', u'支付失败','')
            else:
                error_code =  doc['xml']['err_code']
                error_code_des =  doc['xml']['err_code_des']
                return (False, error_code, error_code_des,'')
        else:
            return_msg = doc['xml']['return_msg']
            return (False, return_code, return_msg,'')

    def get_sign_for_wx(self, para, key):
        '''
        根据算法, 生成微信支付签名
        :param cr:
        :param uid:
        :param para:
        :param context:
        :return:
        '''
        keylist = list(para.keys())
        keylist.sort()
        s = ''
        for i in range(len(keylist)):
            s += str(keylist[i]) + '=' + str(para[keylist[i]])
            if i != len(keylist) - 1:
                s += '&'
        s += '&key=' + key
        signmd5 = hashlib.md5()
        signmd5.update(s)
        sign = (signmd5.hexdigest()).upper()
        return sign

    #拼接xml字符串
    def get_xml_data(self, doc, para):
        root = doc.createElement('xml')
        doc.appendChild(root)
        for key, value in sorted(para.items()):
            new_node = doc.createElement(key)
            node_value = doc.createTextNode(str(value))
            new_node.appendChild(node_value)
            root.appendChild(new_node)
        return doc

