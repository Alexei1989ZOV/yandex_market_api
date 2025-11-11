from base.client import YandexMarketBase
from base.client import BaseReportManager


class SalesReport(BaseReportManager):
    def __init__(self, client: YandexMarketBase):
        super().__init__(client, "sales_analytics")

    def get_sales_report(self, date_from: str, date_to: str, grouping: str = "CATEGORIES"):
        payload = {
            "dateFrom": date_from,
            "dateTo": date_to,
            "grouping": grouping,
            "businessId": self.client._YandexMarketBase__business_id  # Доступ к приватным атрибутам
        }
        params = {"format": "CSV"}
        filename = f"sales_{date_from}_{date_to}_{grouping}.zip"

        return self.generate_and_download_report(
            "reports/shows-sales/generate",
            payload,
            params,
            filename
        )


class DailyStocks(BaseReportManager):
    def __init__(self, client: YandexMarketBase):
        super().__init__(client, "daily_stocks")

    def get_daily_stocks(self, report_date: str, format: str = "CSV"):
        payload = {
            "reportDate" : report_date,
            "campaignId": self.client._YandexMarketBase__campaign_id
        }
        params = {"format": format}
        filename = f"stocks_{report_date}.zip"
        return self.generate_and_download_report(
            "reports/stocks-on-warehouses/generate",
            payload,
            params,
            filename
        )
