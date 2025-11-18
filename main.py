from base.client import YandexMarketBase
from reports.reports import SalesReport, DailyStocks, GoodsMovement
from config.logging_config import setup_logging, get_logger



def movement_example():
    """Пример получения отчета по движению товаров"""
    logger = get_logger(__name__)
    logger.info("🚀 Запуск генерации отчета по движению товаров...")

    client = YandexMarketBase()
    movement = GoodsMovement(client)

    loaded = movement.run_full_pipeline('2025-01-01', '2025-02-28', 'CSV')

    if loaded > 0:
        logger.info("✅ Отчет по движению товаров успешно скачан, распакован, трансформирован!")
    else:
        logger.error("❌ Ошибка при получении отчета по движению товаров")



def main():
    """Основная функция"""
    # ВАЖНО: настраиваем логирование перед всем остальным
    setup_logging()
    logger = get_logger(__name__)

    try:
        logger.info("=== ЗАПУСК ПРИЛОЖЕНИЯ ===")
        movement_example()
        logger.info("=== ВЫПОЛНЕНИЕ ЗАВЕРШЕНО ===")

    except Exception as e:
        logger.exception(f"💥 Критическая ошибка: {e}")


if __name__ == "__main__":
    main()