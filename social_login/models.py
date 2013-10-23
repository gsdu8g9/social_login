# -*- coding: UTF-8 -*-
from django.db import models
from django.contrib.auth.models import User

class SocialLogin(models.Model):
    social_network = models.CharField(u'Социальная сеть', max_length=50)
    social_id = models.CharField(u'ID в Соц. сети', max_length=50)
    user = models.ForeignKey(User)
