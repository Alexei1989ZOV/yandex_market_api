import requests
from config.config import Config

class YandexMarketBase:
    '''Базовый класс для работы с API YandexMarket'''
    def __init__(self):
        self.__api_key = Config.API_KEY
        self.__business_id = Config.BUSINESS_ID
        self.__campaign_id = Config.CAMPAIGN_ID
        self.__base_url = "https://api.partner.market.yandex.ru/v2"

        self.__session = requests.Session()
        self.__session.headers.update({
            'Api-key': self.__api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    def _make_request(self, method, endpoint, **kwargs):
        '''Универсальный метод для отправки запросов'''
        try:
            url = f'{self.__base_url}/{endpoint}'
            response = self.__session.request(method, url, **kwargs)
            if response.status_code != 200:
                print(f'HTTP ошибка: {response.status_code}: {response.text}')
                return None
            data = response.json()
            if data.get('status') == 'OK':
                return data
            else:
                if data.get('errors'):
                    for error in data.get('errors', []):
                        if isinstance(error, dict):
                            for code, message in error.items():
                                print(f'Ошибка API ЯМ - код: {code}, сообщение: {message}!')
                        else:
                            print(f'Ошибка API ЯМ: {error}!')
                else:
                    print('Неизвестная ошибка API')
                return None

        except Exception as e:
            print(f'HTTP Error: {e}')
            return None
        
    def __str__(self):
        return f"Api-key: {self.__api_key[:6]}...{self.__api_key[-4:]}\n" +\
               f"BUSINESS_ID: {self.__business_id}\n" +\
               f"CAMPAIGN_ID: {self.__campaign_id}"
    

