import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from config.config import Config
from base.client import YandexMarketBase



class TestYandexMarketBase(unittest.TestCase):

    def setUp(self):
        """Настройка перед каждым тестом"""
        # Мокаем конфиг
        self.mock_config = Mock()
        self.mock_config.API_KEY = "test_api_key_12345"
        self.mock_config.BUSINESS_ID = "test_business_id"
        self.mock_config.CAMPAIGN_ID = "test_campaign_id"

        # Патчим Config
        self.config_patcher = patch('base.client.Config', self.mock_config)
        self.config_patcher.start()

        self.market_api = YandexMarketBase()

    def tearDown(self):
        """Очистка после каждого теста"""
        self.config_patcher.stop()

    def test_initialization(self):
        """Тест инициализации класса"""
        # Проверяем приватные атрибуты через доступ к сессии
        session_headers = self.market_api._session.headers
        self.assertEqual(session_headers.get('Api-key'), 'test_api_key_12345')
        self.assertEqual(session_headers.get('Content-Type'), 'application/json')
        self.assertEqual(session_headers.get('Accept'), 'application/json')

        # Проверяем базовый URL
        self.assertEqual(self.market_api._YandexMarketBase__base_url, "https://api.partner.market.yandex.ru/v2")

    def test_str_method(self):
        """Тест строкового представления"""
        result = str(self.market_api)
        expected_parts = [
            "Api-key: test_a...2345",
            "BUSINESS_ID: test_business_id",
            "CAMPAIGN_ID: test_campaign_id"
        ]
        for part in expected_parts:
            self.assertIn(part, result)

    @patch('requests.Session.request')
    def test_successful_request(self, mock_request):
        """Тест успешного запроса"""
        # Мокаем успешный ответ
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "result": {"reportId": "123", "data": "test"}
        }
        mock_response.text = ""
        mock_request.return_value = mock_response

        result = self.market_api.make_request('GET', 'test/endpoint')

        expected_data = {
            "status": "OK",
            "result": {"reportId": "123", "data": "test"}
        }
        self.assertEqual(result, expected_data)
        mock_request.assert_called_once_with('GET', 'https://api.partner.market.yandex.ru/v2/test/endpoint')

    @patch('requests.Session.request')
    def test_request_with_errors_in_response(self, mock_request):
        """Тест запроса с ошибками в JSON"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "errors": [
                {"code": "ERROR_1", "message": "Error message 1"},
                {"code": "ERROR_2", "message": "Error message 2"}
            ]
        }
        mock_response.text = ""
        mock_request.return_value = mock_response

        result = self.market_api.make_request('POST', 'test/endpoint')

        self.assertIsNone(result)

    @patch('requests.Session.request')
    def test_http_400_error(self, mock_request):
        """Тест HTTP 400 ошибки"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.json.return_value = {
            "errors": [
                {"code": "VALIDATION_ERROR", "message": "Invalid input"}
            ]
        }
        mock_request.return_value = mock_response

        result = self.market_api.make_request('GET', 'test/endpoint')

        self.assertIsNone(result)

    @patch('requests.Session.request')
    def test_http_401_unauthorized(self, mock_request):
        """Тест HTTP 401 ошибки"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.json.return_value = {
            "errors": [
                {"code": "AUTH_ERROR", "message": "Invalid API key"}
            ]
        }
        mock_request.return_value = mock_response

        result = self.market_api.make_request('GET', 'test/endpoint')

        self.assertIsNone(result)

    @patch('requests.Session.request')
    def test_invalid_json_response(self, mock_request):
        """Тест невалидного JSON в ответе"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_request.return_value = mock_response

        result = self.market_api.make_request('GET', 'test/endpoint')

        self.assertIsNone(result)

    @patch('requests.Session.request')
    def test_network_exception(self, mock_request):
        """Тест сетевого исключения"""
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")

        result = self.market_api.make_request('GET', 'test/endpoint')

        self.assertIsNone(result)

    @patch('requests.Session.request')
    def test_general_exception(self, mock_request):
        """Тест общего исключения"""
        mock_request.side_effect = Exception("Some general error")

        result = self.market_api.make_request('GET', 'test/endpoint')

        self.assertIsNone(result)

    @patch('requests.Session.request')
    def test_unknown_error_with_response_text(self, mock_request):
        """Тест неизвестной ошибки с текстом ответа"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_response.json.return_value = {}  # Нет ошибок в JSON
        mock_request.return_value = mock_response

        result = self.market_api.make_request('GET', 'test/endpoint')

        self.assertIsNone(result)

    @patch('requests.Session.request')
    def test_request_with_kwargs(self, mock_request):
        """Тест запроса с дополнительными параметрами"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "OK", "result": {}}
        mock_response.text = ""
        mock_request.return_value = mock_response

        result = self.market_api.make_request(
            'POST',
            'test/endpoint',
            json={"key": "value"},
            timeout=30,
            params={"param": "value"}
        )

        self.assertIsNotNone(result)
        mock_request.assert_called_once_with(
            'POST',
            'https://api.partner.market.yandex.ru/v2/test/endpoint',
            json={"key": "value"},
            timeout=30,
            params={"param": "value"}
        )

    @patch('requests.Session.request')
    def test_error_with_missing_code_or_message(self, mock_request):
        """Тест ошибки с отсутствующими code или message"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "errors": [
                {"code": "ERROR_ONLY"},  # Нет message
                {"message": "Message only"},  # Нет code
                {}  # Пустой объект
            ]
        }
        mock_response.text = ""
        mock_request.return_value = mock_response

        result = self.market_api.make_request('GET', 'test/endpoint')

        self.assertIsNone(result)

    @patch('requests.Session.request')
    def test_success_with_additional_fields(self, mock_request):
        """Тест успешного запроса с дополнительными полями"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "result": {"id": 123},
            "paging": {"next": "token"}
        }
        mock_response.text = ""
        mock_request.return_value = mock_response

        result = self.market_api.make_request('GET', 'campaigns')

        expected_data = {
            "status": "OK",
            "result": {"id": 123},
            "paging": {"next": "token"}
        }
        self.assertEqual(result, expected_data)

    @patch('requests.Session.request')
    def test_get_campaign_id(self, mock_request):
        """Тест получения campaign_id"""
        campaign_id = self.market_api.get_campaign_id()
        self.assertEqual(campaign_id, "test_campaign_id")

    @patch('requests.Session.request')
    def test_get_business_id(self, mock_request):
        """Тест получения business_id"""
        business_id = self.market_api.get_business_id()
        self.assertEqual(business_id, "test_business_id")


class TestYandexMarketBaseIntegration(unittest.TestCase):
    """Интеграционные тесты (требуют реального API)"""

    @unittest.skip("Требует реального API ключа")
    def test_real_api_connection(self):
        """Тест реального соединения с API (пропускается по умолчанию)"""
        market_api = YandexMarketBase()
        result = market_api.make_request('GET', 'campaigns')
        # Этот тест будет работать только с реальными credentials


if __name__ == '__main__':
    # Запуск тестов с подробным выводом
    unittest.main(verbosity=2)