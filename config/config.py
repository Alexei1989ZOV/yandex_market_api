from dotenv import load_dotenv
import os

load_dotenv()
class Config:
    DATABASE_URL = 'mysql+mysqlconnector://alex:Xby6d4g3@192.168.0.200:3306/ym_test_db'
    #DATABASE_URL = 'sqlite:///./yandex_market.db'
    API_KEY = os.getenv("API_KEY")
    BUSINESS_ID = os.getenv("BUSINESS_ID")
    CAMPAIGN_ID = os.getenv("CAMPAIGN_ID")
    