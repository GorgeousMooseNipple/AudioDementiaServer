import os


class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'so very secret'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATA_LOCATION = os.environ.get('DATA_STORAGE') or None
    LAST_FM_API_KEY = os.environ.get('LAST_FM_API_KEY') or None


class TestConfig:

    SECRET_KEY = "you'll never guess"
    TESTING = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI') or None
