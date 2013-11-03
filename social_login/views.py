# -*- coding: UTF-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.http import Http404
from hashlib import md5

from social_login.social_auth import SocialAuth, AuthError, user_login

def vk_auth(request):
    """
    Получение данных пользователя Vkontakte
    """
    if not request.GET.get('code'):
        return redirect(settings.SOCIAL_LOGIN_ACCESS_DENIED_URL)

    auth_params = {
        'access_token_url': 'https://oauth.vk.com/access_token',
        'user_info_url': 'https://api.vk.com/method/users.get',
        'client_id': settings.SOCIAL_LOGIN_VK_APP_ID,
        'client_secret': settings.SOCIAL_LOGIN_VK_SECRET_KEY,
        'redirect_uri': request.build_absolute_uri(reverse('social_login:vk')),
        'request_method': 'GET', #Метод по которому осуществляются запросы к API
        #Список ключей требуемых для получения "access_token" названия ключей должны соответствовать названиям, используемым при обращении к API
        'get_access_token_params': ('client_id', 'client_secret', 'redirect_uri', 'code',),
        'code': request.GET['code'],
        #Список ключей требуемых для получения информации пользователя названия ключей должны соответствовать названиям, используемым при обращении к API
        #Аттрибуты, неизвестные зарание('uids') можно установить перед вызовом метода get_user_info(), 'access_token' известен из предыдущего метода
        'get_user_info_params': ('fields', 'access_token', 'uids',),
        'fields': 'uid,first_name,last_name',
    }

    try:
        auth_object = SocialAuth(auth_params)
        setattr(auth_object, 'uids', auth_object.get_access_token().get('user_id'))
        result = auth_object.get_user_info()
        #Полученный ответ приводим к стандартному виду
        user_info = result.get('response')[0]
        user_info = {
                'id': user_info['uid'],
                'first_name': user_info['first_name'],
                'last_name': user_info['last_name'],
            }
        return user_login(request, user_info, network='VK')
    except AuthError:
        return redirect(settings.SOCIAL_LOGIN_ACCESS_DENIED_URL)

def odnokl_auth(request):
    """
    Получение данных пользователя Odnoklassniki
    """

    if not request.GET.get('code'):
        return redirect(settings.SOCIAL_LOGIN_ACCESS_DENIED_URL)

    auth_params = {
        'access_token_url': 'http://api.odnoklassniki.ru/oauth/token.do',
        'user_info_url': 'http://api.odnoklassniki.ru/fb.do',
        'client_id': settings.SOCIAL_LOGIN_OK_APP_ID,
        'client_secret': settings.SOCIAL_LOGIN_OK_SECRET_KEY,
        'redirect_uri': request.build_absolute_uri(reverse('social_login:odnokl')),
        'application_key': settings.SOCIAL_LOGIN_OK_PUBLIC_KEY,
        'request_method': 'POST', #Метод по которому осуществляются запросы к API
        #Список ключей требуемых для получения "access_token" названия ключей должны соответствовать названиям, используемым при обращении к API
        'get_access_token_params': ('client_id', 'client_secret', 'redirect_uri', 'code', 'grant_type'),
        'grant_type': 'authorization_code',
        'code': request.GET['code'],
        #Список ключей требуемых для получения информации пользователя названия ключей должны соответствовать названиям, используемым при обращении к API
        #Аттрибуты, неизвестные зарание ('sig') можно установить перед вызовом метода get_user_info(), 'access_token' известен из предыдущего метода
        'get_user_info_params': ('application_key', 'method', 'access_token', 'format', 'sig'),
        'method': 'users.getCurrentUser',
        'format':'JSON',
    }

    try:
        auth_object = SocialAuth(auth_params)
        auth_object.get_access_token()
        #Для получения информации о пользователе, необходимо расчитать хэш и установить соответствующий аттрибут, указанный в 'get_user_info_params'
        string = ''.join('%s=%s' % (key, getattr(auth_object, key)) for key in sorted(['application_key', 'method', 'format']))
        sig = md5(string + md5(auth_object.access_token + auth_object.client_secret).hexdigest()).hexdigest().lower()
        setattr(auth_object, 'sig', sig)
        user_info = auth_object.get_user_info()
        #Полученный ответ приводим к стандартному виду
        user_info = {
                'id': user_info['uid'],
                'first_name': user_info['first_name'],
                'last_name': user_info['last_name'],
            }
        return user_login(request, user_info, network='OK')
    except AuthError, KeyError:
        return redirect(settings.SOCIAL_LOGIN_ACCESS_DENIED_URL)


def fb_auth(request):
    """
    Получение данных пользователя Facebook
    """
    if not request.GET.get('code'):
        return redirect(settings.SOCIAL_LOGIN_ACCESS_DENIED_URL)

    auth_params = {
        'access_token_url': 'https://graph.facebook.com/oauth/access_token',
        'user_info_url': 'https://graph.facebook.com/me',
        'client_id': settings.SOCIAL_LOGIN_FB_APP_ID,
        'client_secret': settings.SOCIAL_LOGIN_FB_SECRET_KEY,
        'redirect_uri': request.build_absolute_uri(reverse('social_login:fb')),
        #Метод по которому осуществляются запросы к API
        'request_method': 'GET',
        'code': request.GET['code'],
        'get_access_token_params': ('client_id', 'client_secret', 'redirect_uri', 'code',),
        'get_user_info_params': ('access_token',),
    }
    try:
        user_info = SocialAuth(auth_params).load()
        return user_login(request, user_info, network='FB')
    except AuthError, KeyError:
        return redirect(settings.SOCIAL_LOGIN_ACCESS_DENIED_URL)