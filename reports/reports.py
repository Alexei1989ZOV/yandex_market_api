from base.client import YandexMarketBase
from base.report_base import BaseReportManager
from database.models import GoodsMovementModel, Sales
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime, date



class SalesReport(BaseReportManager):
    """
    Класс для работы с отчетом 'Аналитика продаж'

    Отчет показывает аналитику продаж за выбранный период
    с группировкой по категориям или товарам.
    """

    def __init__(self, client: YandexMarketBase):
        super().__init__(client, "sales_analytics")
        self.model_name = Sales
        self.logger.info("✅ Инициализирован менеджер отчетов по продажам")

    def get_sales_report(self, date_from: str, date_to: str, grouping: str = "OFFERS") -> bool:
        """
        Получить отчет по аналитике продаж

        Args:
            date_from: Начало периода в формате ГГГГ-ММ-ДД
            date_to: Конец периода в формате ГГГГ-ММ-ДД
            grouping: Группировка данных (OFFERS - по товарам, CATEGORIES - по категориям)

        Returns:
            bool: True если отчет успешно скачан, False в случае ошибки
        """
        self.logger.info(f"📊 Запрос отчета по продажам за период {date_from} - {date_to}, группировка: {grouping}")

        payload = {
            "dateFrom": date_from,
            "dateTo": date_to,
            "grouping": grouping,
            "businessId": self.client.get_business_id()
        }
        params = {"format": "CSV"}
        filename = f"sales_{date_from}_{date_to}_{grouping}.zip"

        self.logger.debug(f"Параметры запроса: {payload}")

        success = self.generate_and_download_report(
            "reports/shows-sales/generate",
            payload,
            params,
            filename
        )

        if success:
            self.logger.info(f"✅ Отчет по продажам успешно сохранен: {filename}")
        else:
            self.logger.error(f"❌ Не удалось получить отчет по продажам за период {date_from}-{date_to}")

        return success

    def run_full_pipeline(self, date_from: str, date_to: str, grouping: str = "OFFERS", format_: str = "CSV") -> int:
        try:
            params = {"format": format_}
            payload = {
                "businessId": self.client.get_business_id(),
                "dateFrom": date_from,
                "dateTo": date_to,
                "grouping": grouping
            }
            extension = "zip" if format_ in ["CSV", "JSON"] else "xlsx"
            filename = f"sales_{date_from}_{date_to}_{format_}.{extension}"

            path = self.generate_and_download_report(
                "reports/shows-sales/generate",
                payload=payload,
                params=params,
                filename=filename
            )

            unzipped_files = self._unzip_archive(path)

            # report_date = datetime.now().strftime('%Y-%m-%d')  # Тут исправить логику даты отчета
            all_records = []

            for file_path in unzipped_files:
                records = self._transform_csv_to_model_data(
                    file_path,
                    self.report_type,
                    report_date=None
                )
                all_records.extend(records)
            if all_records:
                # Предполагаем, что self.model определён в классе
                loaded_count = self._load_to_db(all_records, self.model_name)
                self.logger.info(f"✅ Загружено {loaded_count} записей в БД")
                return loaded_count
            else:
                self.logger.warning("📭 Нет данных для загрузки")
                return 0
        except Exception as e:
            self.logger.error(f"❌ Ошибка в пайплайне: {e}")
            raise


class DailyStocks(BaseReportManager):
    """
    Класс для работы с отчетом 'Остатки на складах'

    Отчет показывает остатки товаров на складах на указанную дату.
    """

    def __init__(self, client: YandexMarketBase):
        super().__init__(client, "daily_stocks")
        self.logger.info("✅ Инициализирован менеджер отчетов по остаткам")

    def get_daily_stocks(self, report_date: str, format: str = "CSV") -> bool:
        """
        Получить отчет по остаткам на складах

        Args:
            report_date: Дата отчета в формате ГГГГ-ММ-ДД
            format: Формат отчета (CSV, FILE, JSON)

        Returns:
            bool: True если отчет успешно скачан, False в случае ошибки
        """
        self.logger.info(f"📦 Запрос отчета по остаткам на дату {report_date}, формат: {format}")

        payload = {
            "reportDate": report_date,
            "campaignId": self.client.get_campaign_id()
        }
        params = {"format": format}

        # Определяем расширение файла
        extension = "zip" if format in ["CSV", "JSON"] else "xlsx"
        filename = f"stocks_{report_date}.{extension}"

        self.logger.debug(f"Параметры запроса: {payload}")

        success = self.generate_and_download_report(
            "reports/stocks-on-warehouses/generate",
            payload,
            params,
            filename
        )

        if success:
            self.logger.info(f"✅ Отчет по остаткам успешно сохранен: {filename}")
        else:
            self.logger.error(f"❌ Не удалось получить отчет по остаткам на дату {report_date}")

        return success


class GoodsMovement(BaseReportManager):
    """
    Класс для работы с отчетом 'Движение товаров'

    Отчет показывает движение товаров (приходы, расходы, перемещения)
    за выбранный период для модели FBY.
    """

    def __init__(self, client: YandexMarketBase):
        super().__init__(client, "goods_movement")
        self.model_name = GoodsMovementModel
        self.logger.info("✅ Инициализирован менеджер отчетов по движению товаров")

    def run_full_pipeline(self, date_from: str, date_to: str, format: str = "CSV") -> int:
        try:
            params = {"format" : format}
            payload  = {
                "campaignId": self.client.get_campaign_id(),
                "dateFrom": date_from,
                "dateTo": date_to    
            }
            extension = "zip" if format in ["CSV", "JSON"] else "xlsx"
            filename = f"goods_movement_{date_from}_{date_to}.{extension}"

            path = self.generate_and_download_report(
                "reports/goods-movement/generate",
                payload=payload,
                params=params,
                filename=filename
            )

            unzipped_files = self._unzip_archive(path)

            report_date = datetime.now().strftime('%Y-%m-%d') # Тут исправить логику даты отчета
            all_records = []

            for file_path in unzipped_files:
                records = self._transform_csv_to_model_data(
                    file_path, 
                    self.report_type, 
                    report_date
                )
                all_records.extend(records)
            if all_records:
                # Предполагаем, что self.model определён в классе
                loaded_count = self._load_to_db(all_records, self.model_name)
                self.logger.info(f"✅ Загружено {loaded_count} записей в БД")
                return loaded_count
            else:
                self.logger.warning("📭 Нет данных для загрузки")
                return 0
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка в пайплайне: {e}")
            raise

           



    def get_goods_movement_with_sku(self, date_from: str, date_to: str, shop_sku: str, format: str = "CSV") -> bool:
        """
        Получить отчет по движению товаров с фильтром по SKU

        Args:
            date_from: Начало периода в формате ГГГГ-ММ-ДД
            date_to: Конец периода в формате ГГГГ-ММ-ДД
            shop_sku: SKU товара для фильтрации
            format: Формат отчета (CSV, FILE, JSON)

        Returns:
            bool: True если отчет успешно скачан, False в случае ошибки
        """
        self.logger.info(f"🔍 Запрос отчета по движению товара {shop_sku} за период {date_from} - {date_to}")

        payload = {
            "campaignId": self.client.get_campaign_id(),
            "dateFrom": date_from,
            "dateTo": date_to,
            "shopSku": shop_sku
        }
        params = {"format": format}

        extension = "zip" if format in ["CSV", "JSON"] else "xlsx"
        filename = f"goods_movement_{date_from}_{date_to}_{shop_sku}.{extension}"

        self.logger.debug(f"Параметры запроса с фильтром SKU: {payload}")

        success = self.generate_and_download_report(
            "reports/goods-movement/generate",
            payload,
            params,
            filename
        )

        if success:
            self.logger.info(f"✅ Отчет по движению товара {shop_sku} успешно сохранен: {filename}")
        else:
            self.logger.error(f"❌ Не удалось получить отчет по движению товара {shop_sku}")

        return success





