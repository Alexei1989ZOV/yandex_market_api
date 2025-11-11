import requests
import logging
from config.config import Config
from config.logging_config import get_logger


class YandexMarketBase:
    '''Базовый класс для работы с API YandexMarket'''

    def __init__(self):
        self.__api_key = Config.API_KEY
        self.__business_id = Config.BUSINESS_ID
        self.__campaign_id = Config.CAMPAIGN_ID
        self.__base_url = "https://api.partner.market.yandex.ru/v2"
        self.logger = get_logger(__name__)

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

            # Логируем детали запроса на DEBUG уровне
            self.logger.debug(f"Request: {method} {url}")

            response = self.__session.request(method, url, **kwargs)

            try:
                data = response.json()
            except ValueError:
                data = {}

            errors = data.get('errors', [])
            has_errors = len(errors) > 0

            if response.status_code == 200 and not has_errors:
                self.logger.debug(f"Success: {method} {endpoint}")
                return data

            # Логируем ошибки
            self.logger.error(f'HTTP {response.status_code} for {method} {endpoint}')

            if has_errors:
                for error in errors:
                    code = error.get('code', 'UNKNOWN_CODE')
                    message = error.get('message', 'No message provided')
                    self.logger.error(f'API Error - code: {code}, message: {message}')
            else:
                self.logger.error('Unknown API error')
                if response.text:
                    self.logger.debug(f'Response text: {response.text}')  # DEBUG для деталей

            return None

        except requests.exceptions.RequestException as e:
            self.logger.exception(f'Network error for {method} {endpoint}: {e}')
            return None
        except Exception as e:
            self.logger.exception(f'Unexpected error for {method} {endpoint}: {e}')
            return None

    def __str__(self):
        return f"Api-key: {self.__api_key[:6]}...{self.__api_key[-4:]}\n" + \
            f"BUSINESS_ID: {self.__business_id}\n" + \
            f"CAMPAIGN_ID: {self.__campaign_id}"