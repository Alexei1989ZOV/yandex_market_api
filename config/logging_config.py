import logging
import sys
from pathlib import Path


def setup_logging():
    """Настройка логгера для всего приложения"""
    # Создаем папку для логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Хендлер для файла
    file_handler = logging.FileHandler(
        log_dir / "yandex_market_api.log",
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Хендлер для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    # Корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def get_logger(name):
    """Получить именованный логгер"""
    return logging.getLogger(name)