import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OSV_API_URL = os.getenv("OSV_API_URL")
    OSV_API_BATCH_URL = os.getenv("OSV_API_BATCH_URL")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "app.log")

settings = Settings()
