import requests
import time
import logging
from typing import Optional, List, Dict
from pathlib import Path
from config.config import Config
from config.logging_config import get_logger
from config.etl_config import REPORT_CONFIGS
import pandas as pd
from requests import Session
from zipfile import ZipFile
from datetime import datetime


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


class BaseReportManager:
    """Базовый класс с общей логикой получения отчетов"""
    def __init__(self, client: YandexMarketBase, report_type: str):
        self.client = client
        self.logger = get_logger(__name__)
        self.report_type = report_type
        self.raw_dir = Path('raw') / report_type
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir = Path('processed') / report_type
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        # Обертка для единообразного логирования бизнес-событий
        self.logger.debug(f"Report request: {method} {endpoint}")
        return self.client.make_request(method, endpoint, **kwargs)


    def _extract_report_id(self, response: dict) -> str:
        """Извлекает report_id из успешного ответа"""
        if "result" not in response:
            raise ValueError("В ответе отсутствует ключ 'result'")
        report_id = response['result'].get('reportId')
        if not report_id:
            raise ValueError("Ключ reportId отсутствует в ответе или пустой")
        if not isinstance(report_id, str):
            raise ValueError(f"reportId должен быть строкой, получен {type(report_id)}")
        return report_id


    def _wait_for_report_completion(self, report_id: str, max_wait_time: int = 600,
                                   check_interval: int = 10) -> str:
        """
        Ожидает завершения генерации отчета, периодически проверяя его статус.

        Args:
            report_id: ID отчета, за которым осуществляется наблюдение
            max_wait_time: Максимальное время ожидания в секундах. По умолчанию 600 (10 минут)
            check_interval: Интервал между проверками статуса в секундах. По умолчанию 10

        Returns:
            URL сгенерированного отчета в случае успеха

        Raises:
            RuntimeError: При ошибке генерации отчета или отсутствии ссылки
            TimeoutError: При превышении времени ожидания

        Examples:
            >>> report_url = client.wait_for_report_completion("report-123")
            >>> download_report(report_url)
        """
        start_time = time.time()
        check_count = 0

        self.logger.info(f"🔄 Начато ожидание отчета {report_id} (макс. {max_wait_time} сек.)")

        while time.time() - start_time < max_wait_time:
            check_count += 1
            data = self._make_request('GET', f'reports/info/{report_id}')
            result = data.get('result', {})
            status = result.get('status')
            elapsed = int(time.time() - start_time)

            if status == 'DONE':
                if result.get('file'):
                    file_url = result.get('file')
                    self.logger.info(f'✅ Отчет готов за {elapsed} сек.: {file_url}')
                    return file_url
                else:
                    self.logger.error('Генерация завершена, но ссылка отсутствует')
                    raise RuntimeError('Генерация завершена, но ссылка отсутствует')

            elif status == 'FAILED':
                sub_status = result.get('subStatus')
                error_msg = f' ({sub_status})' if sub_status else ''
                self.logger.error(f'❌ Генерация отчета провалена{error_msg}')
                raise RuntimeError(f'Генерация отчета провалена{error_msg}')

            elif status in ['PENDING', 'PROCESSING']:
                # Логируем не каждую проверку, чтобы не засорять логи
                if check_count % 5 == 1:  # Каждую 5-ю проверку
                    estimated_time = result.get('estimatedGenerationTime')
                    eta_msg = f", ETA: {estimated_time}ms" if estimated_time else ""
                    self.logger.info(f'⏳ Отчет генерируется... {elapsed} сек.{eta_msg}')
                time.sleep(check_interval)

            else:
                self.logger.warning(f'Неизвестный статус: {status}')
                time.sleep(check_interval)

        self.logger.error(f'⏰ Превышено время ожидания ({max_wait_time} сек.) для отчета {report_id}')
        raise TimeoutError(f'Превышено время ожидания ({max_wait_time} сек.) для отчета {report_id}')

    def _download_report_file(self, file_url: str, filename: str) -> Path:
        """
        Скачивает готовый отчет по URL и сохраняет в файл.

        Args:
            file_url: Прямой URL для скачивания отчета
            filename: Имя файла для сохранения (с расширением)

        Returns:
            Path: Путь к сохраненному файлу

        Raises:
            IOError: При ошибке HTTP-запроса или файловых операций

        Examples:
            >>> file_path = client._download_report_file(
            ...     "https://api.example.com/reports/file123.pdf",
            ...     "sales_report_2024.pdf"
            ... )
            >>> print(f"Отчет сохранен: {file_path}")
            >>> # Теперь можно использовать Path методы:
            >>> file_path.name, file_path.parent
        """
        save_path = self.raw_dir / filename

        try:
            session = self.client.get_session()
            response = session.get(file_url, stream=True)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                self.logger.info(f'📥 Отчет сохранен: {save_path}')
                return save_path
            else:
                self.logger.error(f'Ошибка скачивания: {response.status_code} - {response.text}')
                raise IOError("Произошла ошибка во время скачивания")
        except Exception as e:
            self.logger.error(f'Ошибка при скачивании отчета: {e}')
            raise

    def generate_and_download_report(self, endpoint: str, payload: dict, params: dict, filename: str) -> Path:
        """
        Выполняет полный цикл генерации и скачивания отчета.

        Args:
            endpoint: API endpoint для запуска генерации отчета
            payload: Тело запроса с параметрами генерации отчета
            params: Query-параметры для GET-запроса
            filename: Имя файла для сохранения отчета (с расширением)

        Returns:
            Path к сохраненному отчету

        Examples:
            >>> report_path = client.generate_and_download_report(...)
            >>> print(f"Отчет сохранен: {report_path}")
            >>> # Можно использовать Path методы:
            >>> report_path.name, report_path.parent, report_path.exists()
        """
        # Запускаем генерацию отчета
        data = self._make_request('POST', endpoint, json=payload, params=params)
        report_id = self._extract_report_id(data)
        self.logger.info(f'🚀 Запущена генерация отчета: {report_id}')        
        # Ждем завершения генерации
        file_url = self._wait_for_report_completion(report_id)
        # Скачиваем файл
        return self._download_report_file(file_url, filename)
# Рефакторить дальше отсюда
    def _unzip_archive(self, archive_path: Path, extract_dir: Path = None) -> List[Path]:
        """
            Распаковывает архив с CSV файлами, добавляя временную метку к именам.

            Args:
                archive_path (Path): Путь к архиву для распаковки
                extract_dir (Path, optional): Директория для распаковки.
                                            Если None, используется self.processed_dir

            Returns:
                List[Path]: Список путей к распакованным CSV файлам
            Raises:
                Exception: Если распаковка не удалась
        """
        if extract_dir is None:
            extract_dir = self.processed_dir
        extracted_files = []
        try:
            with ZipFile(archive_path, 'r') as z:
                for file_info in z.filelist:
                    if file_info.filename.endswith(".csv"):
                        # Добавляем временную метку к имени файла
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        original_stem = Path(file_info.filename).stem
                        new_filename = f"{original_stem}_{timestamp}.csv"
                        # Извлекаем с новым именем
                        content = z.read(file_info.filename)
                        new_file_path = extract_dir / new_filename

                        with open(new_file_path, 'wb') as f:
                            f.write(content)
                        extracted_files.append(new_file_path)
                        self.logger.debug(f'📦 Извлечен: {new_filename}')
            return extracted_files
        except Exception as e:
            self.logger.error(f'❌ Ошибка при распаковке {archive_path}: {e}')
            raise



    def list_downloaded_reports(self) -> list[Path]:
        """Получить список всех скачанных отчетов этого типа"""
        return list(self.raw_dir.glob("*"))

    def get_report_path(self, filename: str) -> Path:
        """Получить полный путь к файлу отчета"""
        return self.raw_dir / filename

    def _transform_csv_to_model_data(self, file_path: Path, report_type: str, report_date: str) -> List[Dict]:
        """
                Трансформирует CSV в данные для создания объектов модели

                Args:
                    file_path: Путь к CSV файлу
                    report_type: Тип отчета (ключ в REPORT_CONFIGS)
                    report_date: Дата отчета в формате 'YYYY-MM-DD'

                Returns:
                    List[Dict]: Список словарей с данными для создания объектов модели
        """

        logger = self.logger

        # Получаем конфиг
        config = REPORT_CONFIGS.get(report_type)
        if not config:
            raise ValueError(f"Неизвестный тип отчета: {report_type}")
        columns_config = config.get('columns', {})

        # 1. Проверяем наличие необходимых столбцов
        use_columns = set(columns_config.keys())
        try:
            src_columns = set(pd.read_csv(file_path, nrows=0).columns)
        except Exception as e:
            logger.error(f"❌ Не удалось прочитать файл {file_path}: {e}")
            raise

        missing_columns = use_columns.difference(src_columns)
        if missing_columns:
            error_msg = f"❌ Отсутствуют необходимые столбцы: {missing_columns}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"✅ Все необходимые столбцы присутствуют в {file_path.name}")

        # 2. Читаем CSV
        try:
            src_df = pd.read_csv(
                file_path,
                usecols=list(use_columns),
                dtype={col: 'object' for col in use_columns}
            )
            logger.info(f"📊 Загружено {len(src_df)} строк из {file_path.name}")
        except Exception as e:
            logger.error(f"❌ Ошибка чтения CSV: {e}")
            raise

        # 3. Применяем трансформации данных
        for col_name, col_config in columns_config.items():
            # Заполняем значения по умолчанию
            if 'default' in col_config and src_df[col_name].isna().any():
                default_val = col_config['default']
                src_df[col_name] = src_df[col_name].fillna(default_val)
                logger.debug(f"Применено значение по умолчанию для {col_name}: {default_val}")

            # Приводим к нужному типу
            src_df[col_name] = self._apply_type_transformation(
                src_df[col_name], col_config, col_name
            )

        # 4. Переименовываем столбцы
        columns_mapping = {
            col: col_config.get('field_name', col.lower())
            for col, col_config in columns_config.items()
        }
        src_df = src_df.rename(columns=columns_mapping)

        # 5. Добавляем технические поля
        src_df['report_date'] = pd.to_datetime(report_date).date()

        # 6. Конвертируем в список словарей
        records = src_df.to_dict('records')
        logger.info(f"✅ Трансформировано {len(records)} записей")

        return records


    def _apply_type_transformation(self, series: pd.Series, col_config: Dict, col_name: str) -> pd.Series:
        """Применяет трансформации типа данных к колонке"""
        data_type = col_config.get('type', 'str')

        try:
            if data_type == 'int':
                return pd.to_numeric(series, errors='coerce').fillna(0).astype('int64')

            elif data_type == 'float':
                return pd.to_numeric(series, errors='coerce').fillna(0.0).astype('float64')

            elif data_type == 'decimal':
                return pd.to_numeric(series, errors='coerce').fillna(0.0)

            elif data_type == 'str':
                series = series.astype(str)
                max_length = col_config.get('max_length')
                if max_length:
                    series = series.str.slice(0, max_length)
                return series

            elif data_type == 'date':
                # Обработка дат в формате '10-10-2025'
                return pd.to_datetime(series, format='%d-%m-%Y', errors='coerce')

            else:
                return series

        except Exception as e:
            self.logger.warning(f"⚠️ Ошибка трансформации колонки {col_name}: {e}")
            return series









