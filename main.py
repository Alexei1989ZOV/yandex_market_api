from base.client import YandexMarketBase
from reports.reports import SalesReport, DailyStocks, GoodsMovement
from configs.logging_config import setup_logging, get_logger



def movement_example():
    """Пример получения отчета по движению товаров"""
    logger = get_logger(__name__)
    logger.info("🚀 Запуск генерации отчета по движению товаров...")

    client = YandexMarketBase()
    movement = GoodsMovement(client)

    loaded = movement.run_full_pipeline('2024-12-01', '2025-10-30', 'CSV')

    if loaded > 0:
        logger.info("✅ Отчет по движению товаров успешно скачан, распакован, трансформирован!")
    else:
        logger.error("❌ Ошибка при получении отчета по движению товаров")

def sales_example():
    """Пример получения отчета по движению товаров"""
    logger = get_logger(__name__)
    logger.info("🚀 Запуск генерации отчета по движению товаров...")

    client = YandexMarketBase()
    sales = SalesReport(client)

    loaded = sales.run_full_pipeline('2024-11-01', '2024-12-31', 'OFFERS', 'CSV')

    if loaded > 0:
        logger.info("✅ Отчет по движению товаров успешно скачан, распакован, трансформирован!")
    else:
        logger.error("❌ Ошибка при получении отчета по движению товаров")


def sales_example_missed():
    """Пример получения отчета по движению товаров"""
    logger = get_logger(__name__)
    logger.info("🚀 Запуск генерации отчета по движению товаров...")

    client = YandexMarketBase()
    sales = SalesReport(client)

    # Вариант 1: Загрузить за конкретную дату (как было)
    # loaded = sales.run_full_pipeline('2025-11-27', '2025-11-27', 'OFFERS', 'CSV')

    # Вариант 2: Автоматическая дозагрузка пропущенных отчетов
    stats = sales.run_missing_reports()  # загрузит максимум 3 пропущенных дня

    if stats["loaded"] > 0:
        logger.info(f"✅ Загружено {stats['loaded']} отчетов за даты: {stats['loaded_dates']}")
    else:
        logger.info("📭 Нет отчетов для загрузки или все уже загружены")



def main():
    """Основная функция"""
    # ВАЖНО: настраиваем логирование перед всем остальным
    setup_logging()
    logger = get_logger(__name__)

    try:
        logger.info("=== ЗАПУСК ПРИЛОЖЕНИЯ ===")
        #sales_example()
        sales_example_missed()
        #movement_example()
        logger.info("=== ВЫПОЛНЕНИЕ ЗАВЕРШЕНО ===")


    except Exception as e:
        logger.exception(f"💥 Критическая ошибка: {e}")


if __name__ == "__main__":
    main()