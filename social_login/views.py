# -*- coding: UTF-8 -*-
from django.conf import settings
from social_login.models import SocialLogin
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.http import Http404
from hashlib import md5
import logging
import random
import requests
import json

logger = logging.getLogger('social_login')


def user_login(request, user_info):

    try:
        social_login = SocialLogin.objects.get(social_id=user_info['id'], social_network=user_info['network'])
        user = social_login.user

    except SocialLogin.DoesNotExist:
        user = User.objects.create(
            username=user_info['network'] + str(user_info['id']),
            is_active=True,
            first_name=user_info['first_name'],
            last_name=user_info['last_name']
        )
        password = md5(str(random.randint(1,2000000000))).hexdigest()
        user.set_password(password)
        user.save()
        SocialLogin.objects.create(social_id=user_info['id'], social_network=user_info['network'], user=user)

    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)

    return redirect(settings.SUCCESS_LOGIN_URL) # Перенаправление после удачной авторизации


def vk(request):
    """ "Для Вконтакте обращение к API осуществляется только через метод GET" """
    if request.GET.get('code'):
        code = request.GET['code']
        redirect_url = request.build_absolute_uri(reverse('social_login:vk'))#url по типу 'http://mysite.com/social_login/VK/'
        get_access_token_url = 'https://oauth.vk.com/access_token?client_id=%s&client_secret=%s&code=%s&redirect_uri=%s' \
                           %(settings.VK_APP_ID, settings.VK_SECRET_KEY, code, redirect_url)
        resp = requests.get(get_access_token_url) # Получаем access_token

        if resp.status_code == 200:
            social_user_id = json.loads(resp.text).get('user_id')
            access_token = json.loads(resp.text).get('access_token')

            if not (social_user_id or access_token):
                logger.exception(u'Не удалось получить access_token \n Ответ от https://oauth.vk.com/access_token: ' + resp.text)
                return redirect(settings.USER_ACCESS_DENIED_URL)

            resp = requests.get('https://api.vk.com/method/users.get?uids=%s&fields=uid,first_name,last_name&access_token=%s'\
                                %(social_user_id, access_token))# Получаем личные данные пользователя
            response = json.loads(resp.text).get('response')

            if not response:
                logger.exception(u'Не удалось получить информацию о пользователе \n Ответ от https://api.vk.com/method/users.get: ' + resp.text)
                return redirect(settings.USER_ACCESS_DENIED_URL)
            else:
                user_info = response[0]
                user_info = {
                    'id': user_info['uid'],
                    'first_name': user_info['first_name'],
                    'last_name': user_info['last_name'],
                    'network': 'VK',
                }
                return user_login(request, user_info)

        else:
            logger.exception(u'В ответ от https://oauth.vk.com/access_token получен status_code = %d Ответ содержит:%s' % (resp.status_code, resp.text))
            return redirect(settings.USER_ACCESS_DENIED_URL)
    else:
        logger.exception(u'Не удалось получить code: ' + request.GET)
        return redirect(settings.USER_ACCESS_DENIED_URL)


def ok(request):
    """ "Для Одноклассников обращение к API осуществляется только через метод POST" """
    if request.GET.get('code'):
        code = request.GET['code']
        redirect_url = request.build_absolute_uri(reverse('social_login:ok'))#url по типу 'http://mysite.com/social_login/OK/'
        params = {
            'code': code,
            'redirect_uri': redirect_url ,
            'grant_type': 'authorization_code',
            'client_id': settings.OK_APP_ID,
            'client_secret': settings.OK_SECRET_KEY,
            }
        resp = requests.post('http://api.odnoklassniki.ru/oauth/token.do', data=params) # Получаем access_token

        if resp.status_code == 200:
            access_token = json.loads(resp.text).get('access_token')

            if not access_token:
                logger.exception(u'Не удалось получить access_token \n Ответ от http://api.odnoklassniki.ru/oauth/token.do: ' + resp.text)
                return redirect(settings.USER_ACCESS_DENIED_URL)
            else:
                params = {
                    'sig': md5('application_key=%sformat=JSONmethod=users.getCurrentUser' \
                               % settings.OK_PUBLIC_KEY + md5(access_token+settings.OK_SECRET_KEY).hexdigest()).hexdigest().lower(),
                    'access_token': access_token,
                    'application_key': settings.OK_PUBLIC_KEY,
                    'method': 'users.getCurrentUser',
                    'format':'JSON',
                }
                response = requests.post('http://api.odnoklassniki.ru/fb.do', data=params) # Получаем личные данные пользователя

                if not ('uid' and 'first_name' and 'last_name') in response.text:
                    logger.exception(u'Не удалось получить информацию о пользователе \n Ответ от http://api.odnoklassniki.ru/fb.do: ' + response.text)
                    return redirect(settings.USER_ACCESS_DENIED_URL)
                else:
                    user_info = json.loads(response.text)
                    user_info = {
                        'id': user_info['uid'],
                        'first_name': user_info['first_name'],
                        'last_name': user_info['last_name'],
                        'network':'OK',
                    }
                    return user_login(request,user_info)
        else:
            logger.exception(u'В ответ от http://api.odnoklassniki.ru/oauth/token.do получен status_code = %d Ответ содержит:%s'\
                             % (resp.status_code, resp.text))
            return redirect(settings.USER_ACCESS_DENIED_URL)
    else:
        logger.exception(u'Не удалось получить code: ' + request.GET)
        return redirect(settings.USER_ACCESS_DENIED_URL)


def fb(request):
    """ "Получение данных пользователя Facebook" """
    if request.GET.get('code'):
        code = request.GET['code']
        redirect_url = request.build_absolute_uri(reverse('social_login:fb'))#url по типу 'http://mysite.com/social_login/OK/'
        get_access_token_url = 'https://graph.facebook.com/oauth/access_token?client_id=%s&redirect_uri=%s&client_secret=%s&code=%s'\
                               % (settings.FB_APP_ID, redirect_url, settings.FB_SECRET_KEY, code)
        resp = requests.get(get_access_token_url)# Получаем access_token

        if resp.status_code == 200 and resp.text.startswith('access_token'):
                access_token = [pair.split('=')[1] for pair in resp.text.split('&') if pair.startswith('access_token')][0]
                fb_user_info = requests.get('https://graph.facebook.com/me?access_token='+access_token)# Получаем личные данные пользователя

                if not ('id' and 'first_name' and 'last_name') in fb_user_info.text:
                    logger.exception(u'Не удалось получить информацию о пользователе \n Ответ от https://graph.facebook.com/me: ' + fb_user_info.text)
                else:
                    user_info = json.loads(fb_user_info.text)
                    user_info = {
                        'id': user_info['id'],
                        'first_name': user_info['first_name'],
                        'last_name': user_info['last_name'],
                        'network': 'FB',
                    }
                    return user_login(request,user_info)
        else:
            logger.exception(u'Не удалось получить access_token \n Ответ от https://graph.facebook.com/oauth/access_token: ' + resp.text)
            return redirect(settings.USER_ACCESS_DENIED_URL)
    else:
        logger.exception(u'Не удалось получить code: ' + request.GET)
        return redirect(settings.USER_ACCESS_DENIED_URL)