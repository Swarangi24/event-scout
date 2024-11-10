# config.py
import os


class Config:
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/eventdb')
    SECRET_KEY = os.getenv('SECRET_KEY', '6692a191b7c75f139ddcea9dfc7d1c8f')
