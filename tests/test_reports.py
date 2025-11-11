import unittest
from unittest.mock import MagicMock, patch
from reports.reports import SalesReport, DailyStocks, GoodsMovement
from base.client import YandexMarketBase


class TestReports(unittest.TestCase):
    def setUp(self):
        # Создаем мок клиента
        self.client = MagicMock(spec=YandexMarketBase)
        self.client.get_business_id.return_value = 12345
        self.client.get_campaign_id.return_value = 67890

    # Тесты для SalesReport
    @patch.object(SalesReport, "generate_and_download_report")
    def test_sales_report_success(self, mock_generate):
        """Тест успешного получения отчета продаж"""
        mock_generate.return_value = True
        report = SalesReport(self.client)
        success = report.get_sales_report("2025-01-01", "2025-01-31", "OFFERS")

        self.assertTrue(success)
        mock_generate.assert_called_once()

        # Проверяем параметры вызова
        args, kwargs = mock_generate.call_args
        # endpoint, payload, params, filename передаются как позиционные аргументы
        self.assertEqual(len(args), 4)  # endpoint, payload, params, filename
        self.assertEqual(args[0], "reports/shows-sales/generate")
        self.assertIsInstance(args[1], dict)  # payload
        self.assertIsInstance(args[2], dict)  # params
        self.assertIsInstance(args[3], str)  # filename

    @patch.object(SalesReport, "generate_and_download_report")
    def test_sales_report_default_group_by(self, mock_generate):
        """Тест отчета продаж с параметром groupBy по умолчанию"""
        mock_generate.return_value = True
        report = SalesReport(self.client)
        success = report.get_sales_report("2025-01-01", "2025-01-31")

        self.assertTrue(success)
        mock_generate.assert_called_once()

    @patch.object(SalesReport, "generate_and_download_report")
    def test_sales_report_failure(self, mock_generate):
        """Тест неудачного получения отчета продаж"""
        mock_generate.return_value = False
        report = SalesReport(self.client)
        success = report.get_sales_report("2025-01-01", "2025-01-31")

        self.assertFalse(success)

    @patch.object(SalesReport, "generate_and_download_report")
    def test_sales_report_filename_format(self, mock_generate):
        """Тест формата имени файла для отчета продаж"""
        mock_generate.return_value = True
        report = SalesReport(self.client)
        report.get_sales_report("2025-01-01", "2025-01-31", "OFFERS")

        # Проверяем что filename передается как позиционный аргумент
        args, kwargs = mock_generate.call_args
        self.assertEqual(len(args), 4)
        filename = args[3]  # filename - четвертый позиционный аргумент
        self.assertIsInstance(filename, str)
        self.assertTrue(len(filename) > 0)
        self.assertIn("sales", filename.lower())

    # Тесты для DailyStocks
    @patch.object(DailyStocks, "generate_and_download_report")
    def test_daily_stocks_success(self, mock_generate):
        """Тест успешного получения отчета остатков"""
        mock_generate.return_value = True
        report = DailyStocks(self.client)
        success = report.get_daily_stocks("2025-01-15")

        self.assertTrue(success)
        mock_generate.assert_called_once()

        args, kwargs = mock_generate.call_args
        self.assertEqual(len(args), 4)
        self.assertEqual(args[0], "reports/stocks-on-warehouses/generate")
        self.assertIsInstance(args[1], dict)  # payload
        self.assertIsInstance(args[2], dict)  # params
        self.assertIsInstance(args[3], str)  # filename

    @patch.object(DailyStocks, "generate_and_download_report")
    def test_daily_stocks_failure(self, mock_generate):
        """Тест неудачного получения отчета остатков"""
        mock_generate.return_value = False
        report = DailyStocks(self.client)
        success = report.get_daily_stocks("2025-01-15")

        self.assertFalse(success)

    @patch.object(DailyStocks, "generate_and_download_report")
    def test_daily_stocks_filename_format(self, mock_generate):
        """Тест формата имени файла для отчета остатков"""
        mock_generate.return_value = True
        report = DailyStocks(self.client)
        report.get_daily_stocks("2025-01-15")

        args, kwargs = mock_generate.call_args
        self.assertEqual(len(args), 4)
        filename = args[3]  # filename - четвертый позиционный аргумент
        self.assertIsInstance(filename, str)
        self.assertTrue(len(filename) > 0)
        self.assertIn("stocks", filename.lower())

    # Тесты для GoodsMovement
    @patch.object(GoodsMovement, "generate_and_download_report")
    def test_goods_movement_success(self, mock_generate):
        """Тест успешного получения отчета движения товаров"""
        mock_generate.return_value = True
        report = GoodsMovement(self.client)
        success = report.get_goods_movement("2025-01-01", "2025-01-31")

        self.assertTrue(success)
        mock_generate.assert_called_once()

        args, kwargs = mock_generate.call_args
        self.assertEqual(len(args), 4)
        self.assertEqual(args[0], "reports/goods-movement/generate")
        self.assertIsInstance(args[1], dict)  # payload
        self.assertIsInstance(args[2], dict)  # params
        self.assertIsInstance(args[3], str)  # filename

    @patch.object(GoodsMovement, "generate_and_download_report")
    def test_goods_movement_failure(self, mock_generate):
        """Тест неудачного получения отчета движения товаров"""
        mock_generate.return_value = False
        report = GoodsMovement(self.client)
        success = report.get_goods_movement("2025-01-01", "2025-01-31")

        self.assertFalse(success)

    @patch.object(GoodsMovement, "generate_and_download_report")
    def test_goods_movement_with_sku_success(self, mock_generate):
        """Тест успешного получения отчета движения товаров с SKU"""
        mock_generate.return_value = True
        report = GoodsMovement(self.client)
        success = report.get_goods_movement_with_sku("2025-01-01", "2025-01-31", "SKU123")

        self.assertTrue(success)
        mock_generate.assert_called_once()

    @patch.object(GoodsMovement, "generate_and_download_report")
    def test_goods_movement_with_sku_failure(self, mock_generate):
        """Тест неудачного получения отчета движения товаров с SKU"""
        mock_generate.return_value = False
        report = GoodsMovement(self.client)
        success = report.get_goods_movement_with_sku("2025-01-01", "2025-01-31", "SKU123")

        self.assertFalse(success)

    @patch.object(GoodsMovement, "generate_and_download_report")
    def test_goods_movement_filename_format(self, mock_generate):
        """Тест формата имени файла для отчета движения товаров"""
        mock_generate.return_value = True
        report = GoodsMovement(self.client)
        report.get_goods_movement("2025-01-01", "2025-01-31")

        args, kwargs = mock_generate.call_args
        self.assertEqual(len(args), 4)
        filename = args[3]  # filename - четвертый позиционный аргумент
        self.assertIsInstance(filename, str)
        self.assertTrue(len(filename) > 0)
        self.assertIn("goods", filename.lower())

    @patch.object(GoodsMovement, "generate_and_download_report")
    def test_goods_movement_with_sku_filename_format(self, mock_generate):
        """Тест формата имени файла для отчета движения товаров с SKU"""
        mock_generate.return_value = True
        report = GoodsMovement(self.client)
        report.get_goods_movement_with_sku("2025-01-01", "2025-01-31", "SKU123")

        args, kwargs = mock_generate.call_args
        self.assertEqual(len(args), 4)
        filename = args[3]  # filename - четвертый позиционный аргумент
        self.assertIsInstance(filename, str)
        self.assertTrue(len(filename) > 0)
        self.assertIn("goods", filename.lower())

    # Тесты инициализации
    def test_report_initialization(self):
        """Тест инициализации отчетов"""
        # Создаем отчеты - они должны инициализироваться без ошибок
        sales_report = SalesReport(self.client)
        stocks_report = DailyStocks(self.client)
        movement_report = GoodsMovement(self.client)

        self.assertEqual(sales_report.client, self.client)
        self.assertEqual(stocks_report.client, self.client)
        self.assertEqual(movement_report.client, self.client)

        # Проверяем что правильно устанавливается report_type (используем реальные значения из вашего кода)
        self.assertEqual(sales_report.report_type, "sales_analytics")
        self.assertEqual(stocks_report.report_type, "daily_stocks")  # Исправлено на реальное значение
        self.assertEqual(movement_report.report_type, "goods_movement")

    # Тесты обработки ошибок в параметрах
    @patch.object(SalesReport, "generate_and_download_report")
    def test_sales_report_invalid_dates(self, mock_generate):
        """Тест с некорректными датами"""
        mock_generate.return_value = False
        report = SalesReport(self.client)
        success = report.get_sales_report("invalid-date", "2025-01-31")

        self.assertFalse(success)
        mock_generate.assert_called_once()

    @patch.object(DailyStocks, "generate_and_download_report")
    def test_daily_stocks_empty_date(self, mock_generate):
        """Тест с пустой датой"""
        mock_generate.return_value = False
        report = DailyStocks(self.client)
        success = report.get_daily_stocks("")

        self.assertFalse(success)
        mock_generate.assert_called_once()


class TestReportEdgeCases(unittest.TestCase):
    """Тесты граничных случаев для отчетов"""

    def setUp(self):
        self.client = MagicMock(spec=YandexMarketBase)
        self.client.get_business_id.return_value = 12345
        self.client.get_campaign_id.return_value = 67890

    @patch.object(SalesReport, "generate_and_download_report")
    def test_sales_report_same_dates(self, mock_generate):
        """Тест отчета продаж за один день"""
        mock_generate.return_value = True
        report = SalesReport(self.client)
        success = report.get_sales_report("2025-01-01", "2025-01-01")

        self.assertTrue(success)
        mock_generate.assert_called_once()

    @patch.object(GoodsMovement, "generate_and_download_report")
    def test_goods_movement_long_period(self, mock_generate):
        """Тест отчета движения товаров за длительный период"""
        mock_generate.return_value = True
        report = GoodsMovement(self.client)
        success = report.get_goods_movement("2024-01-01", "2025-01-01")

        self.assertTrue(success)
        mock_generate.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)