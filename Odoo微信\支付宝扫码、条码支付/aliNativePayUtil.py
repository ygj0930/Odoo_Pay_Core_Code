# -*- coding:utf-8 -*-
#author：叶国坚

import socket
import string
import time
import random
import requests
import string
import json
import hashlib
import xmltodict
import sys
import urllib
import urllib2
from datetime import datetime
import re
import json
import re
import rsa
import OpenSSL
import base64

class AliNativePayUtil(object):
    # ========支付相关配置信息===========
    ALIPAY_INPUT_CHARSET = 'utf-8'
    # 合作身份者ID，以2088开头的16位纯数字
    ALIPAY_PARTNER = ''
    # 签约支付宝账号或卖家支付宝帐户
    ALIPAY_SELLER_EMAIL = ''
    # 支付结果回调地址
    ALIPAY_NOTIFY_URL = "服务器ip" + "/aliQRCodeNotify"
    # 访问模式,根据自己的服务器是否支持ssl访问，若支持请选择https；若不支持请选择http
    ALIPAY_TRANSPORT = 'https'
    SIGN_TYPE = "SHA-1"
    #支付宝 应用id
    APP_ID = ''
    #下单api
    precreate_GATEWAY="https://openapi.alipay.com/gateway.do?"


    #获取二维码url
    def getAlipayUrl(self,orderid,goodsName,goodsPrice,**kwargs):
        # 构建公共参数
        params = {}
        params['method'] = 'alipay.trade.precreate'
        params['version'] = '1.0'
        params['app_id'] = self.APP_ID
        params['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        params['charset'] = self.ALIPAY_INPUT_CHARSET
        params['notify_url'] = self.ALIPAY_NOTIFY_URL
        params['sign_type'] = 'RSA2'

        # 构建订单参数
        biz_content = {}
        biz_content['out_trade_no'] = orderid  # 订单号
        biz_content['subject'] = goodsName  #商品名
        biz_content['total_amount'] = goodsPrice  # 价格
        biz_content['timeout_express'] = '1m'  # 1分钟内不支付则关闭
        params['biz_content'] = biz_content

        #由参数，生成签名，并且拼接得到下单参数字符串
        encode_params = self.make_payment_request(params)
        #下单
        url = self.precreate_GATEWAY + encode_params
        response = requests.get(url)
        #提取下单响应
        body = response.text
        #解析下单响应json字符串
        body_dict = json.loads(body)
        return_msg = body_dict['alipay_trade_precreate_response']['msg']
        if return_msg == "Success":
                code_url = body_dict['alipay_trade_precreate_response']['qr_code']
                return code_url
        else:
            print "fail msg=============" + return_msg #打印出错信息


    #===========辅助功能函数======
    #1：生成下单参数字符串
    def make_payment_request(self,params_dict):
        """
        构造支付请求参数
        :param params_dict:
        :return:
        """
        query_str = self.params_to_query(params_dict,)  # 拼接参数字符串
        sign = self.make_sign(query_str)  # 生成签名
        sign = urllib.quote(sign, safe='')
        res = "%s&sign=%s" % (query_str, sign)
        return res
    def params_to_query(self,params):
        """
        生成需要签名的字符串
        :param params:
        :return:
        """
        """
        :param params:
        :return:
        """
        query = ""
        dict_items = {}
        for key, value in params.items():
            if isinstance(value, dict) == True:
                dict_items[key] = value
                params[key] = "%s"
        all_str = ''
        for key in sorted(params.keys()):
            all_str = all_str + '%s=%s&' % (key, params[key])
        all_str = all_str.rstrip('&')
        biz_content_dict = dict_items['biz_content']
        content_str = ''
        for key in sorted(biz_content_dict.keys()):
            if isinstance(biz_content_dict[key], basestring) == True:
                content_str = content_str + '"%s":"%s",' % (key, biz_content_dict[key])
            else:
                content_str = content_str + '"%s":%s,' % (key, biz_content_dict[key])
        content_str = content_str.rstrip(',')
        content_str = '{' + content_str + '}'
        query = all_str % content_str
        return query
    def make_sign(self,para_str):
        """
        签名
        :param message:
        :return:
        """
        private_key = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, open(
            './private_key.txt').read())
        import sys
        reload(sys)
        sys.setdefaultencoding('utf-8')
        sign = base64.encodestring(OpenSSL.crypto.sign(private_key, para_str, 'sha256'))
        return sign









