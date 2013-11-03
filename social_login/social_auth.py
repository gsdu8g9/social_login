# -*- coding: UTF-8 -*-
from social_login.models import SocialLogin
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.conf import settings
import json
import logging
import requests


class AuthError(Exception):
    logger = logging.getLogger('social_login')

    def __init__(self, message):
        self.logger.exception(message)
        Exception.__init__(self, message)


def get_request(request_url, request_params):
    get_string = '?' + '&'.join('%s=%s' % (key, request_params[key]) for key in request_params)
    url = request_url + get_string
    return requests.get(url)


def post_request(request_url, request_params):
    return requests.post(request_url, data=request_params)


class SocialAuth(object):

    def __init__(self, auth_params):
        self.__dict__ = auth_params
        if self.request_method == 'GET':
            self.request_method = get_request
        elif self.request_method == 'POST':
            self.request_method = post_request


    def access_token_handler(self, response):
        """ Обрабатывает ответ, полученный от сервера, cоздает аттрибут "access_token" и возвращает полный ответ для дополнительных манипуляций """
        try:
            response = json.loads(response.text)
            if response.get('access_token'):
                self.access_token = response.get('access_token')
            return response
        except (ValueError, KeyError):
            if response.text.startswith('access_token'):
                access_token = \
                    [pair.split('=')[1] for pair in response.text.split('&') if pair.startswith('access_token')][0]
                self.access_token = access_token
            else:
                message = u'Failed to get the access token \n response from %s: %s' % (
                    self.access_token_url, response.text)
                raise AuthError(message)


    def user_info_handler(self, response):
        """ Обрабатывает ответ, полученный от сервера и возвращает словарь содержащий информацию о пользователе. """
        try:
            return json.loads(response.text)
        except ValueError:
            message = u'Failed to get the user info \n response from %s: %s' % (self.user_info_url, response.text)
            raise AuthError(message)


    def get_access_token(self):
        """ Создает словарь, содержащий параметры запроса. В соответствии с указанным методом запрашивает данные и передает в обработчик """
        request_params = {key: getattr(self, key) for key in self.get_access_token_params}
        response = self.request_method(self.access_token_url, request_params)
        return self.access_token_handler(response)


    def get_user_info(self):
        """ Создает словарь, содержащий параметры запроса. В соответствии с указанным методом запрашивает данные и передает в обработчик """
        request_params = {key: getattr(self, key) for key in self.get_user_info_params}
        response = self.request_method(self.user_info_url, request_params)
        return self.user_info_handler(response)


    def load(self):
        """ Можно вызвать при отсутствии необходимости промежуточной обработки данных между получением токена и получением информации пользователя """
        self.get_access_token()
        return self.get_user_info()


def user_login(request, user_info, network):
    """ Проверяет наличие социального аккаунта в базе после чего, либо создает новый и регистрирует пользователя, либо авторизирует пользователя """
    try:
        social_login = SocialLogin.objects.get(social_id=user_info['id'], social_network=network)
        user = social_login.user

    except SocialLogin.DoesNotExist:
        user = User.objects.create(
            username=network + str(user_info['id']),
            is_active=True,
            first_name=user_info['first_name'],
            last_name=user_info['last_name']
        )
        password = User.objects.make_random_password()
        user.set_password(password)
        user.save()
        SocialLogin.objects.create(social_id=user_info['id'], social_network=network, user=user)

    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
    # Перенаправление после удачной авторизации
    return redirect(settings.SOCIAL_LOGIN_SUCCESS_LOGIN_URL)