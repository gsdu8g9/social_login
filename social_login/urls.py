# -*- coding: UTF-8 -*-
from django.conf.urls import patterns, url

urlpatterns = patterns('social_login.views',
   url(r'^(\w{2})/$', 'social_login', name='login'),
   )