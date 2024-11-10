# tests/test_config.py
import os
from config import Config


class TestConfig(Config):
    MONGO_URI = 'mongodb://localhost:27017/testdb'
    SECRET_KEY = '6692a191b7c75f139ddcea9dfc7d1c8f'
