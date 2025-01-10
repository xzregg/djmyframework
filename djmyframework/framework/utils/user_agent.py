# -*- coding: utf-8 -*-
# @Time    : 2022/5/25 09:44 
# @Author  : xzr
# @File    : user_agent.py
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    :
from user_agents.parsers import UserAgent

from framework.utils.attribute import CacheAttribute
import weakref

class RequestUserAgent(UserAgent):

    def __init__(self, request):
        ua_string = request.META.get('HTTP_USER_AGENT', '')
        super().__init__(ua_string)
        self.ua_string = self.ua_string.lower()
        self.request = weakref.proxy(request)

    @CacheAttribute
    def is_wechat(self):
        return ('wechat' in self.ua_string or 'micromessenger' in self.ua_string ) and not self.is_wechat_mini and not self.is_qy_wechat

    @CacheAttribute
    def is_wechat_mini(self):
        return self.request.POST.get('ua') == 'wx_miniapp'

    @CacheAttribute
    def is_qy_wechat(self):
        return 'wxwork' in self.ua_string


    @CacheAttribute
    def is_dingtalk(self):
        return 'dingtalk' in self.ua_string

    @CacheAttribute
    def is_alipay(self):
        return 'alipay' in self.ua_string and not self.is_alipay_mini

    @CacheAttribute
    def is_alipay_mini(self):
        # 靠客户端传
        #return ('alipay' in self.ua_string and 'alipayclient' in self.ua_string) or self.request.POST.get('ua') == 'alipay_miniapp'
        return self.request.POST.get('ua') == 'alipay_miniapp'

    @CacheAttribute
    def is_bankabc_mini(self):
        # 靠客户端传
        # return ('alipay' in self.ua_string and 'alipayclient' in self.ua_string) or self.request.POST.get('ua') == 'alipay_miniapp'
        return self.request.POST.get('ua') == 'abc_miniapp'

    @CacheAttribute
    def is_bankabc(self):
        return 'bankabc' in self.ua_string

    @CacheAttribute
    def is_h5(self):
        return not any([self.is_alipay, self.is_alipay_mini, self.is_wechat, self.is_wechat_mini])

    @CacheAttribute
    def is_wecard(self):
        return self.request.POST.get('ua') == 'wecard'

    @CacheAttribute
    def is_psbc(self):
        """邮储H5"""
        return 'psbc' in self.ua_string

    @CacheAttribute
    def is_unionpay(self):
        """云闪付H5"""
        return 'unionpay' in self.ua_string

    @CacheAttribute
    def is_bestpay(self):
        """翼支付H5"""
        return 'bestpay' in self.ua_string

