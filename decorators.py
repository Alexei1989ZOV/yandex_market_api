import time
from datetime import datetime
from functools import wraps


def rate_limit(requests_per_hour: int = 10):
    """
    Декоратор для ограничения количества вызовов функции в час.

    Args:
        requests_per_hour: максимальное количество вызовов в час
    """

    def decorator(func):
        # Храним историю вызовов
        call_history = []

        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            hour_ago = current_time - 3600

            # Удаляем старые вызовы (старше часа)
            call_history[:] = [t for t in call_history if t > hour_ago]

            # Проверяем лимит
            if len(call_history) >= requests_per_hour:
                # Находим когда можно будет сделать следующий вызов
                next_call_time = call_history[0] + 3600
                wait_time = max(0, next_call_time - current_time)

                if wait_time > 0:
                    print(f"⏳ Лимит {requests_per_hour}/час достигнут. Ждем {wait_time:.0f} сек...")
                    time.sleep(wait_time)
                    # Обновляем время после ожидания
                    current_time = time.time()

            # Добавляем текущий вызов в историю
            call_history.append(current_time)

            # Вызываем оригинальную функцию
            return func(*args, **kwargs)

        return wrapper

    return decorator