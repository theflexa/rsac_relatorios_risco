import os
from dotenv import load_dotenv

load_dotenv()

JARBIS_URL = os.getenv("JARBIS_BASE_URL")
JARBIS_USER = os.getenv("JARBIS_USERNAME")
JARBIS_PASSWORD = os.getenv("JARBIS_PASSWORD")

LOGIN_USER = os.getenv("LOGIN_USER")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD")
