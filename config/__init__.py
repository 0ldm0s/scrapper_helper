# -*- coding: utf-8 -*-
import os

basedir = os.path.abspath(os.path.dirname(__file__))
MIO_HOST = os.environ.get('MIO_HOST', '127.0.0.1')
MIO_PORT = int(os.environ.get('MIO_PORT', 5050))
MIO_SITE_HOST = os.environ.get('MIO_SITE_HOST', MIO_HOST)
RENEW_KEY: str = "config:renew"
XVFB_KEY: str = "config:xvfb"
MOBILE_KEY: str = "config:mobile"
HEADLESS_KEY: str = "config:headless"
BLACK_KEYWORDS_KEY: str = "config:black_keywords"


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'PYMIO_SECRET_KEY'  # 默认秘钥
    SESSION_TYPE = 'filesystem'
    # 邮件系统设置相关
    MIO_MAIL = False
    MIO_SEND_MAIL = False
    MAIL_SUBJECT_PREFIX = os.environ.get('MIO_MAIL_SUBJECT_PREFIX', '[Mio System]')  # 默认邮件标题前缀
    MAIL_DEFAULT_SENDER = \
        os.environ.get('MIO_MAIL_DEFAULT_SENDER', 'Mio System Administrator <admin@example.com>')  # 默认发件人
    MAIL_SERVER = os.environ.get('MIO_MAIL_SERVER', 'localhost')
    MAIL_PORT = os.environ.get('MIO_MAIL_PORT', 25)
    MAIL_USE_TLS = os.environ.get('MIO_MAIL_USE_TLS', False)
    MAIL_USE_SSL = os.environ.get('MIO_MAIL_USE_SSL', False)
    MAIL_USERNAME = os.environ.get('MIO_MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MIO_MAIL_PASSWORD', '')
    # 是否使用MONGODB
    MONGODB_ENABLE = os.environ.get('MIO_MONGODB_ENABLE', True)
    # 是否使用CELERY
    CELERY_ENABLE = os.environ.get('MIO_CELERY_ENABLE', True)
    # 是否使用Redis
    REDIS_ENABLE = os.environ.get('MIO_REDIS_ENABLE', True)
    # Redis前导
    REDIS_KEY_PREFIX = 'scrapper'
    # 是否使用CACHE
    CACHED_ENABLE = os.environ.get('MIO_CACHED_ENABLE', True)
    # 是否使用CORS
    CORS_ENABLE = os.environ.get('MIO_CORS_ENABLE', False)
    CORS_URI = os.environ.get('MIO_CORS_URI', {r"/*": {"origins": "*"}})
    # 支持的语言
    LANGUAGES = ['zh-CN']
    # 默认语言
    DEFAULT_LANGUAGE = 'zh-CN'
    # 默认时区
    MIO_TIMEZONE = 'Asia/Shanghai'

    @staticmethod
    def init_app(app):
        app.jinja_env.trim_blocks = True
        app.jinja_env.lstrip_blocks = True


class DevelopmentConfig(Config):
    DEBUG = True
    MONGODB_SETTINGS = {
        'db': 'scrapper',
        'host': 'mongodb://scrapper:scrapper@172.16.0.83/scrapper?compressors=zstd,snappy,zlib',
        'connect': False
    }
    MQ_URI = "amqp://scrapper:scrapper@172.16.0.83/scrapper"
    REDIS_URL = "redis://172.16.0.83:6379/0"
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = REDIS_URL
    CELERY_BROKER_URL = MQ_URI
    CELERY_RESULT_BACKEND = MQ_URI
    CELERY_BACKEND_URL = REDIS_URL


class TestingConfig(Config):
    TESTING = True
    MONGODB_SETTINGS = {
        'db': 'db_name',
        'host': 'localhost',
        'username': 'username',
        'password': 'password',
        'connect': False
    }
    REDIS_URL = 'redis://localhost:6379/0'
    CACHE_TYPE = 'simple'
    CACHE_REDIS_URL = REDIS_URL
    CELERY_BROKER_URL = REDIS_URL
    CELERY_BACKEND_URL = REDIS_URL


class ProductionConfig(Config):
    MONGODB_SETTINGS = {
        'db': 'db_name',
        'host': 'localhost',
        'username': 'username',
        'password': 'password',
        'connect': False
    }
    REDIS_URL = 'redis://localhost:6379/0'
    CACHE_TYPE = 'simple'
    CACHE_REDIS_URL = REDIS_URL
    CELERY_BROKER_URL = REDIS_URL
    CELERY_BACKEND_URL = REDIS_URL


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
