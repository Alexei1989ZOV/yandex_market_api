import requests
from configs.config_project import Config
from configs.logging_config import get_logger
from requests import Session


class YandexMarketBase:
    '''Базовый класс для работы с API YandexMarket'''

    def __init__(self):
        self.__api_key = Config.API_KEY
        self.__business_id = Config.BUSINESS_ID
        self.__campaign_id = Config.CAMPAIGN_ID
        self.__base_url = "https://api.partner.market.yandex.ru/v2"
        self.logger = get_logger(__name__)

        self._session = requests.Session()
        self._session.headers.update({
            'Api-key': self.__api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """
        Выполняет HTTP-запрос к API Яндекс.Маркета.
        
        Returns:
            dict: Данные ответа API
            
        Raises:
            Exception: При любых ошибках запроса
        """
        try:
            url = f'{self.__base_url}/{endpoint}'
            self.logger.debug(f"Request: {method} {url}")

            response = self._session.request(method, url, **kwargs)

            try:
                data = response.json()
            except ValueError:
                data = {}

            errors = data.get('errors', [])
            has_errors = len(errors) > 0

            if response.status_code == 200 and not has_errors:
                self.logger.debug(f"Success: {method} {endpoint}")
                return data

            # Создаем информативное исключение вместо просто ValueError
            if has_errors:
                error_messages = []
                for error in errors:
                    code = error.get('code', 'UNKNOWN_CODE')
                    message = error.get('message', 'No message provided')
                    error_messages.append(f"{code}: {message}")
                
                error_msg = f"HTTP {response.status_code} - API Errors: {', '.join(error_messages)}"
                raise Exception(error_msg)
            else:
                error_msg = f"HTTP {response.status_code} for {method} {endpoint}"
                if response.text:
                    error_msg += f" - Response: {response.text}"
                raise Exception(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f'Network error for {method} {endpoint}: {e}'
            self.logger.exception(error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            self.logger.exception(f'Unexpected error for {method} {endpoint}: {e}')
            raise

    def __str__(self):
        return f"Api-key: {self.__api_key[:6]}...{self.__api_key[-4:]}\n" + \
            f"BUSINESS_ID: {self.__business_id}\n" + \
            f"CAMPAIGN_ID: {self.__campaign_id}"

    def get_campaign_id(self):
        return self.__campaign_id

    def get_business_id(self):
        return self.__business_id

    def get_session(self) -> Session:
        """
        Возвращает экземпляр requests.Session для прямых запросов.
        ⚠️ Использовать только для чтения (GET-запросы, стриминг файлов).
        """
        return self._session









