from base.client import YandexMarketBase
from base.client import BaseReportManager
from pathlib import Path


class SalesReport(BaseReportManager):
    """
    Класс для работы с отчетом 'Аналитика продаж'

    Отчет показывает аналитику продаж за выбранный период
    с группировкой по категориям или товарам.
    """

    def __init__(self, client: YandexMarketBase):
        super().__init__(client, "sales_analytics")
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
        self.logger.info("✅ Инициализирован менеджер отчетов по движению товаров")

    def get_goods_movement(self, date_from: str, date_to: str, format: str = "CSV") -> bool:
        """
        Получить отчет по движению товаров

        Args:
            date_from: Начало периода в формате ГГГГ-ММ-ДД
            date_to: Конец периода в формате ГГГГ-ММ-ДД
            format: Формат отчета (CSV, FILE, JSON)

        Returns:
            bool: True если отчет успешно скачан, False в случае ошибки
        """
        self.logger.info(f"🔄 Запрос отчета по движению товаров за период {date_from} - {date_to}, формат: {format}")

        payload = {
            "campaignId": self.client.get_campaign_id(),
            "dateFrom": date_from,
            "dateTo": date_to
        }
        params = {"format": format}

        # Определяем расширение файла
        extension = "zip" if format in ["CSV", "JSON"] else "xlsx"
        filename = f"goods_movement_{date_from}_{date_to}.{extension}"

        self.logger.debug(f"Параметры запроса: {payload}")

        success = self.generate_and_download_report(
            "reports/goods-movement/generate",
            payload,
            params,
            filename
        )

        if success:
            self.logger.info(f"✅ Отчет по движению товаров успешно сохранен: {filename}")
        else:
            self.logger.error(f"❌ Не удалось получить отчет по движению товаров за период {date_from}-{date_to}")

        return success

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

    def get_goods_movement_unz(self, date_from: str, date_to: str, format: str = "CSV") -> bool:
        """
        Получить отчет по движению товаров

        Args:
            date_from: Начало периода в формате ГГГГ-ММ-ДД
            date_to: Конец периода в формате ГГГГ-ММ-ДД
            format: Формат отчета (CSV, FILE, JSON)

        Returns:
            bool: True если отчет успешно скачан, False в случае ошибки
        """
        self.logger.info(f"🔄 Запрос отчета по движению товаров за период {date_from} - {date_to}, формат: {format}")

        payload = {
            "campaignId": self.client.get_campaign_id(),
            "dateFrom": date_from,
            "dateTo": date_to
        }
        params = {"format": format}

        # Определяем расширение файла
        extension = "zip" if format in ["CSV", "JSON"] else "xlsx"
        filename = f"goods_movement_{date_from}_{date_to}.{extension}"

        self.logger.debug(f"Параметры запроса: {payload}")

        is_downloaded = self.generate_and_download_report(
            "reports/goods-movement/generate",
            payload,
            params,
            filename
        )

        if not is_downloaded:
            self.logger.error(f"❌ Не удалось скачать отчет по движению товаров за период {date_from}-{date_to}")
            return False
        if format in ["CSV", "JSON"]:
            archive_path = self.raw_dir / filename
            is_unzipped = self._unzip_archive(archive_path)

            if is_unzipped:
                self.logger.info(f"✅ Отчет по движению товаров успешно скачан и распакован: {filename}")
                return True
            else:
                self.logger.error(f"❌ Отчет скачан, но не удалось распаковать: {filename}")
                return False
        else:
            # Для не-архивных форматов просто возвращаем успех скачивания
            self.logger.info(f"✅ Отчет по движению товаров успешно сохранен: {filename}")
            return True


