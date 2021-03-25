# -*- coding: utf-8 -*-

from framework.route import Route
from framework.views import render_to_response,api_get
from django.contrib import messages

@Route()
@api_get()
def index(request):
    a=3
    messages.info(request,'asdkasl;kd')
    return render_to_response('ws_gateway/index.html', locals())
