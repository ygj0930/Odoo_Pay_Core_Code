# -*- coding:utf-8 -*-
#author：叶国坚
#qq：1042336570

import os
import datetime
import time
from jinja2 import Environment, FileSystemLoader
from odoo import http
from odoo.http import request
from cStringIO import StringIO
import base64
import json
from datetime import datetime
from decimal import Decimal
import socket
import qrcode
from io import BytesIO
from weixinNativePayUtil import *
from aliNativePayUtil import *
from weixinMicroPayUtil import *
from aliMicroPayUtil import *

class MainController(http.Controller):
    #=======支付相关==========
    #=======微信二维码支付==============
    @http.route('/getWeixinQRCode', auth='public', csrf=False)
    def getWeixinQRCode(self, **kwargs):
        order_id = kwargs.get('order_id')  #客户端生成的订单号
        goodsName = kwargs.get('goodsName')
        goodsPrice = int(float(kwargs.get('goodsPrice')) * 100)
       
        toolUtil = WeixinNativePayUtil()
        code_url=toolUtil.getPayUrl(order_id,goodsName,goodsPrice)
        if code_url:
            res_info = code_url
            # 如果成功获得支付链接，则写入一条订单记录
            #todo
        else:
            res_info = "二维码失效"
        
        #生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=1
        )
        qr.add_data(res_info)
        img = qr.make_image()
        byte_io = BytesIO()
        img.save(byte_io, 'PNG')
        byte_io.seek(0)
        return http.send_file(byte_io, mimetype='image/png')

    #微信二维码支付回调
    @http.route('/weChatQRCodeNotify', auth='public', csrf=False)
    def weChatQRCodeNotify(self, request, *args,**kwargs):
        order_result_xml = http.request.httprequest.stream.read()
        doc = xmltodict.parse(order_result_xml)
        out_trade_no = doc['xml']['out_trade_no']
        result_code = doc['xml']['result_code']
        #修改订单记录支付状态，根据订单号来修改
        #todo
        return      '''
                    <xml>
                      <return_code><![CDATA[SUCCESS]]></return_code>
                      <return_msg><![CDATA[OK]]></return_msg>
                    </xml>
                    '''

    #=========支付宝二维码支付==========
    @http.route('/getAliQRCode', auth='public', csrf=False)
    def getAliQRCode(self, **kwargs):
        order_id = kwargs.get('order_id') #客户端生成的订单号
        goodsName = kwargs.get('goodsName')
        goodsPrice = float(kwargs.get('goodsPrice'))
    
        toolUtil = AliNativePayUtil()
        code_url=toolUtil.getAlipayUrl(order_id,goodsName,goodsPrice)
        if code_url:
            res_info = code_url
            # 如果成功获得支付链接，则写入一条订单记录
            #todo
        else:
            res_info = "二维码失效"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=1
        )
        qr.add_data(res_info)
        img = qr.make_image()
        byte_io = BytesIO()
        img.save(byte_io, 'PNG')
        byte_io.seek(0)
        return http.send_file(byte_io, mimetype='image/png')

    #支付宝二维码支付回调
    @http.route('/aliQRCodeNotify', auth='public', csrf=False)
    def aliQRCodeNotify(self, request, *args,**kwargs):
        out_trade_no = kwargs.get("out_trade_no")
        trade_status = kwargs.get("trade_status")
        # 修改订单记录支付状态，根据订单号来修改
        if trade_status == "TRADE_SUCCESS":
            #todo：支付成功的后续逻辑
        elif trade_status == "TRADE_CLOSED":
            #todo：支付失败的后续逻辑

    #==========微信、支付宝条码支付========
    @http.route('/doMicroPay', auth='public', csrf=False)
    def doMicroPay(self, **kwargs):
        goodsName = kwargs.get('goodsName')
        goodsPrice = kwargs.get('goodsPrice')
        auth_code = kwargs.get('auth_code')
        pure_order_id = kwargs.get('order_id') #客户端生成的随机字符串
        micro_type = kwargs.get('micro_type')
        order_id = micro_type + pure_order_id #根据支付类型，拼接出具体的订单号

        pay_isSubmit = None
        if(micro_type == "WXMC"): #微信条码支付
            toolUtil = WeixinMicroPayUtil()
            pay_isSubmit = toolUtil.do_weixinMicroPay(order_id, goodsName, float(goodsPrice),auth_code)
        elif(micro_type == "AliMC"): #支付宝条码支付
            toolUtil = AliMicroPayUtil()
            pay_isSubmit = toolUtil.do_aliMicroPay(order_id, goodsName, goodsPrice, auth_code)
        if pay_isSubmit == True:  # 如果成功提交了订单
            state = u'未支付'
        else:  #提交失败，则该种支付方式失败
            state = u'支付失败'
        # 写入一条订单记录
        #todo


    #=====客户端对二维码支付结果轮询========
    @http.route('/getQRCodePayResult', auth='public', csrf=False)
    def getQRCodePayResult(self, **kwargs):
        wx_qrcode_order = kwargs.get('wx_qrcode_order')
        ali_qrcode_order = kwargs.get('ali_qrcode_order')

        # 二维码支付记录查询
        wx_qrcode_order_record = 根据订单号查询出微信二维码支付对应的订单记录
        ali_qrcode_order_record = 根据订单号查询出支付宝二维码支付对应的订单记录
        #得到两种二维码支付记录的支付状态
        wx_qrcode_order_state = wx_qrcode_order_record.state
        ali_qrcode_order_state = ali_qrcode_order_record.state

        if wx_qrcode_order_state == u"支付成功":
            # 微信二维码支付成功
            #删除支付宝二维码订单记录（因为选择了微信支付，所以支付宝的二维码支付订单就多余了）
            #todo：支付成功的后续操作
        elif wx_qrcode_order_state == u"支付失败":
            # 微信二维码支付失败
            #删除支付宝二维码订单记录（因为选择了微信支付，所以支付宝的二维码支付订单就多余了）
            #todo：支付失败的后续操作

        if ali_qrcode_order_state == u"支付成功":
            # 支付宝二维码支付成功
            #删除微信二维码订单记录（因为选择了支付宝支付，所以微信的二维码支付订单就多余了）
            #todo：支付成功的后续操作
        elif ali_qrcode_order_state == u"支付失败":
            # 支付宝二维码支付失败
            #删除微信二维码订单记录（因为选择了支付宝支付，所以微信的二维码支付订单就多余了）
            #todo：支付失败的后续操作

    #====微信、支付宝条码支付结果轮询=====
    @http.route('/getMicroPayResult', auth='public', csrf=False)
    def getMicroPayResult(self, **kwargs):
        pure_order_id = kwargs.get('order_id')
        micro_type = kwargs.get('micro_type')
        order = micro_type + pure_order_id  # 根据支付类型，拼接出具体的订单号
        
        #查询支付结果
        pay_isSuccess=None
        pay_result_code=None
        pay_result_des=None
        buyer=None
        if (micro_type == "WXMC"):  #查询微信条码支付
            toolUtil = WeixinMicroPayUtil()
            (pay_isSuccess, pay_result_code, pay_result_des, buyer) = toolUtil.do_weixinMicroPay_query(order)
        elif (micro_type == "AliMC"):  # 查询支付宝条码支付
            toolUtil = AliMicroPayUtil()
            (pay_isSuccess, pay_result_code, pay_result_des, buyer) = toolUtil.do_aliMicroPay_query(order)
        #根据返回的信息，进行支付成功、支付失败的响应操作，或者支付中的继续轮询
