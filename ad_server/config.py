import os
from dotenv import load_dotenv


PWD = os.path.dirname(os.path.abspath(__file__))
load_dotenv()


class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MEDIA_STORAGE = os.environ.get('MEDIA_STORAGE') or\
        os.path.join(PWD, 'media_storage')
    LAST_FM_API_KEY = os.environ.get('LAST_FM_API_KEY')


class TestConfig(Config):

    SECRET_KEY = "you'll never guess"
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI')
    SONGS_URLS = os.environ.get('SONGS_URLS')
