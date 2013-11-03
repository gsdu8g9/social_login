# -*- coding: UTF-8 -*-
from django import template
from django.core.urlresolvers import reverse
from django.conf import settings
register = template.Library()

@register.tag(name="auth_url")
def auth_link(parser, token):
    try:
        tag_name, network = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a one argument: network_name" % token.contents.split()[0])
    return AuthLinkNode(network)

class AuthLinkNode(template.Node):
    def __init__(self, network):
        self.network = network
    def render(self, context):
        request = context['request']
        if self.network == 'vk':
            link = u'https://oauth.vk.com/authorize?client_id=%s&scope=photos&response_type=code&v=5.2&redirect_uri=%s'\
                   % (settings.SOCIAL_LOGIN_VK_APP_ID, request.build_absolute_uri(reverse('social_login:vk')))
            return link

        elif self.network == 'odnokl':
            link = u'http://www.odnoklassniki.ru/oauth/authorize?client_id=%s&scope=PHOTO CONTENT;SET STATUS&response_type=code&redirect_uri=%s'\
                   % (settings.SOCIAL_LOGIN_OK_APP_ID, request.build_absolute_uri(reverse('social_login:odnokl')))
            return link

        elif self.network == 'fb':
            link = u'https://www.facebook.com/dialog/oauth?client_id=%s&response_type=code&redirect_uri=%s'\
                   % (settings.SOCIAL_LOGIN_FB_APP_ID, request.build_absolute_uri(reverse('social_login:fb')))
            return link