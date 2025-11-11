from base.client import YandexMarketBase
from reports.reports import SalesReport, DailyStocks
from config.logging_config import setup_logging, get_logger


def sales_report_example():
    """Пример получения отчета по продажам"""
    logger = get_logger(__name__)
    logger.info("🚀 Запуск генерации отчета по продажам...")

    client = YandexMarketBase()
    sales_report = SalesReport(client)

    success = sales_report.get_sales_report(
        date_from="2025-01-04",
        date_to="2025-01-04",
        grouping="OFFERS"
    )

    if success:
        logger.info("✅ Отчет по продажам успешно скачан!")
        reports = sales_report.list_downloaded_reports()
        logger.info(f"📁 Файлы в папке sales_analytics: {[r.name for r in reports]}")
    else:
        logger.error("❌ Ошибка при получении отчета по продажам")


def stocks_report_example():
    """Пример получения отчета по остаткам"""
    logger = get_logger(__name__)
    logger.info("🚀 Запуск генерации отчета по остаткам...")

    client = YandexMarketBase()
    stocks = DailyStocks(client)

    success = stocks.get_daily_stocks('2025-11-09')

    if success:
        logger.info("✅ Отчет по остаткам успешно скачан!")
        reports = stocks.list_downloaded_reports()
        logger.info(f"📁 Файлы в папке daily_stocks: {[r.name for r in reports]}")
    else:
        logger.error("❌ Ошибка при получении отчета по остаткам")


def main():
    """Основная функция"""
    # ВАЖНО: настраиваем логирование перед всем остальным
    setup_logging()
    logger = get_logger(__name__)

    try:
        logger.info("=== ЗАПУСК ПРИЛОЖЕНИЯ ===")

        # Запускаем оба отчета
        stocks_report_example()
        logger.info("\n" + "=" * 50)
        sales_report_example()

        logger.info("=== ВЫПОЛНЕНИЕ ЗАВЕРШЕНО ===")

    except Exception as e:
        logger.exception(f"💥 Критическая ошибка: {e}")


if __name__ == "__main__":
    main()