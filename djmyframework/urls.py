"""myadmin URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import re

from django.urls import include, re_path
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.documentation import include_docs_urls


from framework.route import get_urlpatterns
from framework.utils import import_view
from settings import settings
from config.api_doc import urlpatterns as api_doc_urlpatterns


from django.urls import path

from framework.static import serve as static_view
from framework.views import notauth
from django.conf.urls import url
from django.contrib import admin

urlpatterns = [  # url(r'^admin/', admin.site.urls),
                  re_path('^[/]?$', import_view(settings.INDEX_VIEW), name='index'),
                  # 静态资源
                  re_path(r'^%s(?P<path>.*)$' % re.escape(settings.STATIC_URL.lstrip('/')), static_view)
              ] + get_urlpatterns() + api_doc_urlpatterns

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),

        # For django versions before 2.0:
        # url(r'^__debug__/', include(debug_toolbar.urls)),

    ]
