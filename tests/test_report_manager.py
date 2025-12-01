import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from base.client import YandexMarketBase
from base.report_base import BaseReportManager


class TestBaseReportManager(unittest.TestCase):

    def setUp(self):
        """Настройка перед каждым тестом"""
        # Мокаем клиент
        self.mock_client = Mock(spec=YandexMarketBase)
        self.mock_client._session = Mock()

        # Создаем временную директорию для тестов
        self.test_dir = tempfile.mkdtemp()

        # Патчим raw директорию чтобы использовать временную
        with patch('base.client.Path') as mock_path:
            mock_raw_dir = Path(self.test_dir) / 'raw' / 'test_report'
            mock_raw_dir.mkdir(parents=True, exist_ok=True)
            mock_path.return_value.__truediv__.return_value = mock_raw_dir

            self.report_manager = BaseReportManager(self.mock_client, 'test_report')
            self.raw_dir = mock_raw_dir

    def tearDown(self):
        """Очистка после каждого теста"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_initialization(self):
        """Тест инициализации BaseReportManager"""
        self.assertEqual(self.report_manager.report_type, 'test_report')
        self.assertEqual(self.report_manager.client, self.mock_client)
        self.assertEqual(str(self.report_manager.raw_dir), str(self.raw_dir))

    def test_extract_report_id_success(self):
        """Тест извлечения report_id из успешного ответа"""
        test_data = {
            "result": {
                "reportId": "test_report_123"
            }
        }
        report_id = self.report_manager._extract_report_id(test_data)
        self.assertEqual(report_id, "test_report_123")

    def test_extract_report_id_no_result(self):
        """Тест извлечения report_id когда нет result"""
        test_data = {"status": "OK"}
        report_id = self.report_manager._extract_report_id(test_data)
        self.assertIsNone(report_id)

    def test_extract_report_id_no_report_id(self):
        """Тест извлечения report_id когда нет reportId"""
        test_data = {
            "result": {
                "status": "DONE"
            }
        }
        report_id = self.report_manager._extract_report_id(test_data)
        self.assertIsNone(report_id)

    @patch('base.client.time.sleep')
    @patch('base.client.time.time')
    def test_wait_for_report_completion_success(self, mock_time, mock_sleep):
        """Тест успешного ожидания завершения отчета"""
        # Делаем mock_time бесконечным — сначала 1000, потом всегда +5
        start = 1000
        times = [start]

        def fake_time():
            times[0] += 5
            return times[0]

        mock_time.side_effect = fake_time

        self.mock_client.make_request.side_effect = [
            {"result": {"status": "PROCESSING"}},
            {"result": {"status": "DONE", "file": "https://example.com/report.csv"}}
        ]

        file_url = self.report_manager.wait_for_report_completion("test_report_123", max_wait_time=30)

        self.assertEqual(file_url, "https://example.com/report.csv")
        self.assertEqual(self.mock_client.make_request.call_count, 2)

    @patch('base.client.time.sleep')
    @patch('base.client.time.time')
    def test_wait_for_report_completion_failed(self, mock_time, mock_sleep):
        """Тест ожидания когда отчет провалился"""
        # Возвращаем текущее время, которое перестаёт меняться после второго вызова
        mock_time.side_effect = [1000, 1005] + [1005] * 100

        self.mock_client.make_request.return_value = {
            "result": {"status": "FAILED", "subStatus": "GENERATION_FAILED"}
        }

        file_url = self.report_manager.wait_for_report_completion("test_report_123")

        self.assertIsNone(file_url)

    @patch('base.client.time.sleep')
    @patch('base.client.time.time')
    def test_wait_for_report_completion_timeout(self, mock_time, mock_sleep):
        """Тест таймаута ожидания отчета"""
        # Первый вызов time.time() возвращает start_time, второй - время превышающее таймаут
        mock_time.side_effect = [1000, 1601]  # start_time=1000, current_time=1601 (>600)

        self.mock_client.make_request.return_value = {
            "result": {"status": "PROCESSING"}
        }

        file_url = self.report_manager.wait_for_report_completion("test_report_123", max_wait_time=600)

        self.assertIsNone(file_url)

    @patch('base.client.time.sleep')
    def test_wait_for_report_completion_no_response(self, mock_sleep):
        """Тест когда API не возвращает данные"""
        # Используем реальное время но мокаем sleep
        self.mock_client.make_request.return_value = None

        # Устанавливаем очень маленькие таймауты для быстрого теста
        file_url = self.report_manager.wait_for_report_completion(
            "test_report_123",
            max_wait_time=0.1,  # 100ms
            check_interval=0.01  # 10ms
        )

        self.assertIsNone(file_url)

    def test_download_report_file_success(self):
        """Тест успешного скачивания отчета"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"test,data\n", b"1,2\n"]
        self.mock_client._session.get.return_value = mock_response

        result = self.report_manager.download_report_file(
            "https://example.com/report.csv",
            "test_report.csv"
        )

        self.assertTrue(result)
        expected_file = self.raw_dir / "test_report.csv"
        self.assertTrue(expected_file.exists())

        with open(expected_file, 'rb') as f:
            content = f.read()
        self.assertEqual(content, b"test,data\n1,2\n")

    def test_download_report_file_failure(self):
        """Тест неудачного скачивания отчета"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        self.mock_client._session.get.return_value = mock_response

        result = self.report_manager.download_report_file(
            "https://example.com/report.csv",
            "test_report.csv"
        )

        self.assertFalse(result)

    def test_download_report_file_network_error(self):
        """Тест ошибки сети при скачивании"""
        self.mock_client._session.get.side_effect = Exception("Network error")

        result = self.report_manager.download_report_file(
            "https://example.com/report.csv",
            "test_report.csv"
        )

        self.assertFalse(result)

    @patch.object(BaseReportManager, 'wait_for_report_completion')
    @patch.object(BaseReportManager, 'download_report_file')
    def test_generate_and_download_report_success(self, mock_download, mock_wait):
        """Тест успешной генерации и скачивания отчета"""
        self.mock_client.make_request.return_value = {
            "result": {"reportId": "test_report_123"}
        }
        mock_wait.return_value = "https://example.com/report.csv"
        mock_download.return_value = True

        result = self.report_manager.generate_and_download_report(
            "reports/test", {"param": "value"}, {"format": "CSV"}, "report.csv"
        )

        self.assertTrue(result)
        self.mock_client.make_request.assert_called_once()
        mock_wait.assert_called_once_with("test_report_123")
        mock_download.assert_called_once_with("https://example.com/report.csv", "report.csv")

    def test_generate_and_download_report_failed_generation(self):
        """Тест когда генерация отчета не запустилась"""
        self.mock_client.make_request.return_value = None

        result = self.report_manager.generate_and_download_report(
            "reports/test", {}, {}, "report.csv"
        )

        self.assertFalse(result)

    def test_generate_and_download_report_no_report_id(self):
        """Тест когда не удалось извлечь report_id"""
        self.mock_client.make_request.return_value = {
            "result": {"status": "OK"}
        }

        result = self.report_manager.generate_and_download_report(
            "reports/test", {}, {}, "report.csv"
        )

        self.assertFalse(result)

    def test_list_downloaded_reports(self):
        """Тест получения списка скачанных отчетов"""
        test_files = ["report1.csv", "report2.csv"]
        for filename in test_files:
            file_path = self.raw_dir / filename
            file_path.write_text("test data")

        reports = self.report_manager.list_downloaded_reports()

        self.assertEqual(len(reports), 2)
        self.assertIn("report1.csv", [r.name for r in reports])
        self.assertIn("report2.csv", [r.name for r in reports])

    def test_get_report_path(self):
        """Тест получения пути к файлу отчета"""
        expected_path = self.raw_dir / "test_report.csv"
        actual_path = self.report_manager.get_report_path("test_report.csv")

        self.assertEqual(actual_path, expected_path)

    def test_make_request_wrapper(self):
        """Тест обертки для запросов"""
        self.mock_client.make_request.return_value = {"status": "OK"}

        result = self.report_manager._make_request('GET', 'test/endpoint')

        self.assertEqual(result, {"status": "OK"})
        self.mock_client.make_request.assert_called_once_with('GET', 'test/endpoint')


if __name__ == '__main__':
    unittest.main(verbosity=2)