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

    def make_request(self, method: str, endpoint:str, **kwargs) -> dict | None:
        '''Универсальный метод для отправки запросов'''
        try:
            url = f'{self.__base_url}/{endpoint}'

            # Логируем детали запроса на DEBUG уровне
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

            # Логируем ошибки
            self.logger.error(f'HTTP {response.status_code} for {method} {endpoint}')

            if has_errors:
                for error in errors:
                    code = error.get('code', 'UNKNOWN_CODE')
                    message = error.get('message', 'No message provided')
                    self.logger.error(f'API Error - code: {code}, message: {message}')
            else:
                self.logger.error('Unknown API error')
                if response.text:
                    self.logger.debug(f'Response text: {response.text}')  # DEBUG для деталей

            return None

        except requests.exceptions.RequestException as e:
            self.logger.exception(f'Network error for {method} {endpoint}: {e}')
            return None
        except Exception as e:
            self.logger.exception(f'Unexpected error for {method} {endpoint}: {e}')
            return None

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

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict | None:
        # Обертка для единообразного логирования бизнес-событий
        self.logger.debug(f"Report request: {method} {endpoint}")
        return self.client.make_request(method, endpoint, **kwargs)


    def _extract_report_id(self, result: dict) -> str | None:
        """Извлечение report_id из успешного ответа"""
        if result and "result" in result:
            return result['result'].get('reportId')
        return None

    def wait_for_report_completion(self, report_id: str, max_wait_time: int = 600,
                                   check_interval: int = 10) -> str | None:
        """Ожидание завершения генерации отчета с таймаутом"""
        start_time = time.time()
        check_count = 0

        self.logger.info(f"🔄 Начато ожидание отчета {report_id} (макс. {max_wait_time} сек.)")

        while time.time() - start_time < max_wait_time:
            check_count += 1
            data = self._make_request('GET', f'reports/info/{report_id}')

            if not data:
                self.logger.warning(f'Попытка {check_count}: не удалось получить статус отчета')
                time.sleep(check_interval)
                continue

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
                    return None

            elif status == 'FAILED':
                sub_status = result.get('subStatus')
                error_msg = f' ({sub_status})' if sub_status else ''
                self.logger.error(f'❌ Генерация отчета провалена{error_msg}')
                return None

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
        return None

    def download_report_file(self, file_url: str, filename: str) -> bool:
        """Скачивание готового отчета в папку raw/тип_отчета/"""
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
                return True
            else:
                self.logger.error(f'Ошибка скачивания: {response.status_code} - {response.text}')
                return False
        except Exception as e:
            self.logger.error(f'Ошибка при скачивании отчета: {e}')
            return False

    def generate_and_download_report(self, endpoint: str,payload: dict, params: dict, filename: str) -> bool:
        """Универсальный метод для генерации и скачивания отчета"""
        # Запускаем генерацию отчета
        data = self._make_request('POST', endpoint, json=payload, params=params)
        if not data:
            self.logger.error('Не удалось запустить генерацию отчета')
            return False

        report_id = self._extract_report_id(data)
        if not report_id:
            self.logger.error('Не удалось извлечь report_id из ответа')
            return False

        self.logger.info(f'🚀 Запущена генерация отчета: {report_id}')

        # Ждем завершения
        file_url = self.wait_for_report_completion(report_id)
        if not file_url:
            return False

        # Скачиваем файл
        return self.download_report_file(file_url, filename)

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

        logger = logging.getLogger(__name__)

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
            logger = logging.getLogger(__name__)
            logger.warning(f"⚠️ Ошибка трансформации колонки {col_name}: {e}")
            return series









