# -*- coding: UTF-8 -*-
from django.conf.urls import patterns, url

urlpatterns = patterns('social_login.views',
   url(r'^vk/$', 'vk_auth', name='vk'),
   url(r'^odnokl/$', 'odnokl_auth', name='odnokl'),
   url(r'^fb/$', 'fb_auth', name='fb'),
   )