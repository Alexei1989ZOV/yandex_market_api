from base.client import YandexMarketBase
from base.report_base import BaseReportManager
from database.models import GoodsMovementModel, Sales
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime, date
from decorators import rate_limit


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

    @rate_limit()
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


    def run_missing_reports(
            self,
            grouping: str = "OFFERS",
            max_days_per_run: int = None  # Опциональное ограничение
    ) -> dict:
        """
        Автоматически находит и загружает пропущенные отчеты.
        Лимиты API контролируются декоратором @rate_limit.

        Args:
            grouping: группировка данных
            max_days_per_run: максимум дней для загрузки за один запуск

        Returns:
            dict: статистика загрузки
        """
        stats = {
            "total_missing": 0,
            "loaded": 0,
            "failed": 0,
            "loaded_dates": [],
            "failed_dates": [],
            "errors": []
        }

        try:
            # 1. Находим пропущенные даты
            missing_dates = self.get_missing_dates_simple(self.model_name)
            stats["total_missing"] = len(missing_dates)

            if not missing_dates:
                self.logger.info("🎉 Все отчеты уже загружены!")
                return stats

            self.logger.info(f"📋 Найдено {len(missing_dates)} пропущенных дат")

            # 2. Ограничиваем количество дней если нужно
            if max_days_per_run and len(missing_dates) > max_days_per_run:
                dates_to_load = missing_dates[:max_days_per_run]
                remaining = len(missing_dates) - max_days_per_run
                self.logger.info(
                    f"Ограничение: загрузим {max_days_per_run} из {len(missing_dates)} дней. "
                    f"Осталось: {remaining}"
                )
            else:
                dates_to_load = missing_dates

            # 3. Загружаем отчеты
            self.logger.info(f"🚀 Начинаем загрузку {len(dates_to_load)} отчетов...")

            for date_str in dates_to_load:
                try:
                    self.logger.info(f"📅 Загрузка отчета за {date_str}")

                    # Декоратор @rate_limit сам позаботится об ожидании!
                    loaded = self.run_full_pipeline(
                        date_from=date_str,
                        date_to=date_str,
                        grouping=grouping,
                        format_="CSV"
                    )

                    if loaded > 0:
                        stats["loaded"] += 1
                        stats["loaded_dates"].append(date_str)
                        self.logger.info(f"✅ Отчет за {date_str} загружен ({loaded} записей)")
                    else:
                        stats["failed"] += 1
                        stats["failed_dates"].append(date_str)
                        stats["errors"].append(f"{date_str}: нет данных")
                        self.logger.warning(f"⚠️ Нет данных за {date_str}")

                except Exception as e:
                    stats["failed"] += 1
                    stats["failed_dates"].append(date_str)
                    error_msg = f"{date_str}: {str(e)}"
                    stats["errors"].append(error_msg)
                    self.logger.error(f"❌ Ошибка загрузки отчета за {date_str}: {e}")
                    # Продолжаем со следующей датой

            # 4. Итоги
            summary_msg = f"""
            {'=' * 50}
            ИТОГИ АВТОЗАГРУЗКИ:
            {'=' * 50}
            Всего пропущенных дат: {stats['total_missing']}
            Обработано: {len(dates_to_load)}
            Успешно: {stats['loaded']}
            С ошибками: {stats['failed']}
            {'=' * 50}
            """

            self.logger.info(summary_msg)

            return stats

        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка в run_missing_reports: {e}")
            stats["errors"].append(f"Критическая ошибка: {str(e)}")
            return stats


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





