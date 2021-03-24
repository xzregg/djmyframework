# -*- coding: utf-8 -*-

from framework.route import Route
from framework.views import render_to_response,api_get


@Route()
@api_get()
def index(request):
    a=3
    return render_to_response('ws_gateway/index.html', locals())
