from dotenv import load_dotenv
import os

load_dotenv()
class Config:
    DATABASE_URL = 'sqlite:///./yandex_market.db'
    API_KEY = os.getenv("API_KEY")
    BUSINESS_ID = os.getenv("BUSINESS_ID")
    CAMPAIGN_ID = os.getenv("CAMPAIGN_ID")
    