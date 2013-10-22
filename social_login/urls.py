# -*- coding: UTF-8 -*-
from django.conf.urls import patterns, url

urlpatterns = patterns('social_login.views',
   url(r'^vk/$', 'vk', name='vk'),
   url(r'^ok/$', 'ok', name='ok'),
   url(r'^fb/$', 'fb', name='fb'),
   )