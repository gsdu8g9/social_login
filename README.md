social_login
============

Authorization through facebook.com, vk.com, odnoklassniki.ru for Django site 

Для работы приложения необходимо в settings.py добавить следующие переменные:<br>
Выдаются при регистрации приложения в соц. сети<br>
VK_SECRET_KEY = 'ksSDFsDFsdfsfdsdfsdfSDF'   // VK.COM<br>
VK_APP_ID = '1111111'       <br>                    

OK_PUBLIC_KEY = 'CFCFCFCFFCFCFCFCFCCF' // odmiklassniki.ru <br>
OK_SECRET_KEY = 'KJH34535U34H53JNRTI3Y'<br>
OK_APP_ID = '1111111'<br>

FB_APP_ID = '11111111111111111' // facebook.com<br>
FB_SECRET_KEY = 's7d6fhscs76tsdf8s7fy8sd7fns7d8'<br>

USER_ACCESS_DENIED_URL = 'app_namespace:view_name'//URL на который будет переадресован пользователь при неудачной регистрации<br>
SUCCESS_LOGIN_URL = 'app_namespace:view_name'//URL на который будет переадресован пользователь успешной регистрации<br>

И добавляем 'social_login' в INSTALLED_APPS<br>

Далее в social_login/views.py нужно импортировать ваши настройки<br>
from myproject import settings<br>
так же нужно настроить логгер для записи ошибок возникающих при обращении к API<br>
И определить переменную logger = logging.getLogger('logger_name') в тех же views.py<br>

После чего в шаблоне добавляем кнопки перехода к авторизации через соцсети:<br>
&lt;a href=&quot;https://oauth.vk.com/authorize?client_id={VK_APP_ID}&scope=photos&redirect_uri=http://domain.name/social_login/VK/&response_type=code&v=5.2 &quot;&gt;Вход через vk&lt;/a&gt;<br>
&lt;a href=&quot;http://www.odnoklassniki.ru/oauth/authorize?client_id={OK_APP_ID}&scope=PHOTO CONTENT&response_type=code&redirect_uri=http://domain.name/social_login/OK/ &quot;&gt;Вход через Одноклассники&lt;/a&gt;<br>
&lt;a href=&quot;https://www.facebook.com/dialog/oauth?client_id={FB_APP_ID}&redirect_uri=http://domain.name/social_login/FB/&response_type=code &quot;&gt;Вход через Facebook&lt;/a&gt;<br>
domain.name должен быть такой же какой вы указали при регистрации приложения<br>

При первом входе через соц сеть создается новый пользователь с username=social_network_name+social_network_id и рандомным паролем first_name и last_name берутся из соц сети<br>
При повторном  входе при подтверждении авторизации через соц сеть находим пользователя и логиним<br>
Если пользователь отказал в запрашиваемых правах доступа к личной информации, он перенаправляется на USER_ACCESS_DENIED_URL<br>
