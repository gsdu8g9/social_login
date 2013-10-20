Для работы приложения необходимо в settings.py добавить следующие переменные:
// Выдаются при регистрации приложения в соц. сети
VK_SECRET_KEY = 'ksSDFsDFsdfsfdsdfsdfSDF'   // VK.COM
VK_APP_ID = '1111111'                           

OK_PUBLIC_KEY = 'CFCFCFCFFCFCFCFCFCCF' // odmiklassniki.ru
OK_SECRET_KEY = 'KJH34535U34H53JNRTI3Y'
OK_APP_ID = '1111111'

FB_APP_ID = '11111111111111111' // facebook.com
FB_SECRET_KEY = 's7d6fhscs76tsdf8s7fy8sd7fns7d8'

USER_ACCESS_DENIED_URL = 'app_namespace:view_name'//URL на который будет переадресован пользователь при неудачной регистрации
SUCCESS_LOGIN_URL = 'app_namespace:view_name'//URL на который будет переадресован пользователь успешной регистрации

И добавляем 'social_login' в INSTALLED_APPS

Далее в social_login/views.py нужно импортировать ваши настройки
from myproject import settings
так же нужно настроить логгер для записи ошибок возникающих при обращении к API
И определить переменную logger = logging.getLogger('logger_name') в тех же views.py

После чего в шаблоне добавляем кнопки перехода к авторизации через соцсети:
<a href="https://oauth.vk.com/authorize?client_id={VK_APP_ID}&scope=photos&redirect_uri=http://domain.name/social_login/VK/&response_type=code&v=5.2">Вход через vk</a>
<a href="http://www.odnoklassniki.ru/oauth/authorize?client_id={OK_APP_ID}&scope=PHOTO CONTENT&response_type=code&redirect_uri=http://domain.name/social_login/OK/">Вход через Одноклассники</a>
<a href="https://www.facebook.com/dialog/oauth?client_id={FB_APP_ID}&redirect_uri=http://domain.name/social_login/FB/&response_type=code">Вход через Facebook</a>
domain.name должен быть такой же какой вы указали при регистрации приложения

При первом входе через соц сеть создается новый пользователь с username=social_network_name+social_network_id и рандомным паролем first_name и last_name берутся из соц сети
При повторном  входе при подтверждении авторизации через соц сеть находим пользователя и логиним
Если пользователь отказал в запрашиваемых правах доступа к личной информации, он перенаправляется на USER_ACCESS_DENIED_URL
