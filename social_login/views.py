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
        password = password = User.objects.make_random_password()
        user.set_password(password)
        user.save()
        SocialLogin.objects.create(social_id=user_info['id'], social_network=user_info['network'], user=user)

    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
    # Перенаправление после удачной авторизации
    return redirect(settings.SOCIAL_LOGIN_SUCCESS_LOGIN_URL)


def vk_auth(request):
    """ "Для Вконтакте обращение к API осуществляется только через метод GET" """
    if request.GET.get('code'):
        code = request.GET['code']
        #url по типу 'http://mysite.com/social_login/VK/'
        redirect_url = request.build_absolute_uri(reverse('social_login:vk'))
        get_access_token_url = 'https://oauth.vk.com/access_token?client_id=%s&client_secret=%s&code=%s&redirect_uri=%s' \
                           %(settings.SOCIAL_LOGIN_VK_APP_ID, settings.SOCIAL_LOGIN_VK_SECRET_KEY, code, redirect_url)
        # Получаем access_token
        resp = requests.get(get_access_token_url)

        if resp.status_code == 200:
            social_user_id = json.loads(resp.text).get('user_id')
            access_token = json.loads(resp.text).get('access_token')

            if not (social_user_id or access_token):
                logger.exception(u'Не удалось получить access_token \n Ответ от https://oauth.vk.com/access_token: ' + resp.text)
                return redirect(settings.SOCIAL_LOGIN_ACCESS_DENIED_URL)
            # Получаем личные данные пользователя
            resp = requests.get('https://api.vk.com/method/users.get?uids=%s&fields=uid,first_name,last_name&access_token=%s'\
                                %(social_user_id, access_token))
            response = json.loads(resp.text).get('response')

            if not response:
                logger.exception(u'Не удалось получить информацию о пользователе \n Ответ от https://api.vk.com/method/users.get: ' + resp.text)
                return redirect(settings.SOCIAL_LOGIN_ACCESS_DENIED_URL)
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
            return redirect(settings.SOCIAL_LOGIN_ACCESS_DENIED_URL)
    else:
        logger.exception(u'Не удалось получить code: ' + request.GET)
        return redirect(settings.SOCIAL_LOGIN_ACCESS_DENIED_URL)


def ok_auth(request):
    """ "Для Одноклассников обращение к API осуществляется только через метод POST" """
    if request.GET.get('code'):
        code = request.GET['code']
        #url по типу 'http://mysite.com/social_login/OK/'
        redirect_url = request.build_absolute_uri(reverse('social_login:ok'))
        params = {
            'code': code,
            'redirect_uri': redirect_url ,
            'grant_type': 'authorization_code',
            'client_id': settings.SOCIAL_LOGIN_OK_APP_ID,
            'client_secret': settings.SOCIAL_LOGIN_OK_SECRET_KEY,
            }
        # Получаем access_token
        resp = requests.post('http://api.odnoklassniki.ru/oauth/token.do', data=params)

        if resp.status_code == 200:
            access_token = json.loads(resp.text).get('access_token')

            if not access_token:
                logger.exception(u'Не удалось получить access_token \n Ответ от http://api.odnoklassniki.ru/oauth/token.do: ' + resp.text)
                return redirect(settings.SOCIAL_LOGIN_ACCESS_DENIED_URL)
            else:
                params = {
                    'sig': md5('application_key=%sformat=JSONmethod=users.getCurrentUser' \
                               % settings.SOCIAL_LOGIN_OK_PUBLIC_KEY + md5(access_token+settings.SOCIAL_LOGIN_OK_SECRET_KEY).hexdigest()).hexdigest().lower(),
                    'access_token': access_token,
                    'application_key': settings.SOCIAL_LOGIN_OK_PUBLIC_KEY,
                    'method': 'users.getCurrentUser',
                    'format':'JSON',
                }
                # Получаем личные данные пользователя
                response = requests.post('http://api.odnoklassniki.ru/fb.do', data=params)

                if not ('uid' and 'first_name' and 'last_name') in response.text:
                    logger.exception(u'Не удалось получить информацию о пользователе \n Ответ от http://api.odnoklassniki.ru/fb.do: ' + response.text)
                    return redirect(settings.SOCIAL_LOGIN_ACCESS_DENIED_URL)
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
            return redirect(settings.SOCIAL_LOGIN_ACCESS_DENIED_URL)
    else:
        logger.exception(u'Не удалось получить code: ' + request.GET)
        return redirect(settings.SOCIAL_LOGIN_ACCESS_DENIED_URL)


def fb_auth(request):
    """ "Получение данных пользователя Facebook" """
    if request.GET.get('code'):
        code = request.GET['code']
        #url по типу 'http://mysite.com/social_login/OK/'
        redirect_url = request.build_absolute_uri(reverse('social_login:fb'))
        get_access_token_url = 'https://graph.facebook.com/oauth/access_token?client_id=%s&redirect_uri=%s&client_secret=%s&code=%s'\
                               % (settings.SOCIAL_LOGIN_FB_APP_ID, redirect_url, settings.SOCIAL_LOGIN_FB_SECRET_KEY, code)
        # Получаем access_token
        resp = requests.get(get_access_token_url)

        if resp.status_code == 200 and resp.text.startswith('access_token'):
                access_token = [pair.split('=')[1] for pair in resp.text.split('&') if pair.startswith('access_token')][0]
                # Получаем личные данные пользователя
                fb_user_info = requests.get('https://graph.facebook.com/me?access_token='+access_token)

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
            return redirect(settings.SOCIAL_LOGIN_ACCESS_DENIED_URL)
    else:
        logger.exception(u'Не удалось получить code: ' + request.GET)
        return redirect(settings.SOCIAL_LOGIN_ACCESS_DENIED_URL)