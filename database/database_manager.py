from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from configs.config_project import Config
from database.models import Base
from contextlib import contextmanager
from sqlalchemy.orm import DeclarativeBase
from datetime import date, datetime


class DatabaseManager:
    """
    Менеджер для работы с базой данных.

    Предоставляет:
        - Инициализацию движка SQLAlchemy.
        - Управление сессиями через контекстный менеджер.
        - Создание всех таблиц из моделей.
        - Массовую вставку данных в таблицу (bulk insert без ORM flush на каждую запись).
    """

    def __init__(self):
        """
        Инициализирует подключение к базе данных.

        Создает:
            - engine — соединение с БД.
            - SessionLocal — фабрику сессий SQLAlchemy.
        """
        self.engine = create_engine(Config.DATABASE_URL)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)

    def create_tables(self):
        """
        Создаёт все таблицы в базе данных, основываясь на моделях SQLAlchemy.

        Используется обычно один раз при старте приложения.
        """
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def get_session(self):
        """
        Контекстный менеджер для корректной работы с сессией SQLAlchemy.

        Yields:
            session (Session): Активная сессия базы данных.

        Обеспечивает:
            - commit при отсутствии ошибок;
            - rollback при исключении;
            - гарантированное закрытие сессии после выхода из блока.

        Пример:
            >>> db = DatabaseManager()
            >>> with db.get_session() as session:
            ...     session.add(model_obj)
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def bulk_insert(self, model: type[DeclarativeBase], records: list[dict]) -> int:
        """
        Массовая вставка данных в таблицу.

        Args:
            model (Base): ORM-модель SQLAlchemy, представляющая таблицу.
            records (list[dict]): Список словарей, каждый из которых соответствует строке таблицы.

        Returns:
            int: Количество вставленных строк.

        Raises:
            Exception: Любые ошибки SQLAlchemy во время вставки (перехватываются и пробрасываются выше).

        Пример:
            >>> inserted = db.bulk_insert(OrderModel, records)
            >>> print(inserted)
        """
        with self.get_session() as db:
            objects = [model(**record) for record in records]
            db.add_all(objects)
            return len(objects)
