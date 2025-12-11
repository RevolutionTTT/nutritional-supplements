# config.py
import os
from datetime import timedelta
from dotenv import load_dotenv
from urllib.parse import quote_plus

# 加载 ..env 文件
load_dotenv()

class Config:
    # 基础配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'nutrition-secret-key-2024')

    # 数据库配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'nutrition_supplement_db')

    # 如果密码包含特殊字符，需要 urlencode
    MYSQL_PASSWORD_ENC = quote_plus(MYSQL_PASSWORD)

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD_ENC}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT配置
    JWT_SECRET_KEY = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # 文件上传配置
    UPLOAD_FOLDER = 'static/images/products'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # 邮件配置
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.qq.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@nutrition.com')

    # 支付配置（模拟）
    WECHAT_PAY_APPID = os.getenv('WECHAT_PAY_APPID', 'mock_appid')
    ALIPAY_APPID = os.getenv('ALIPAY_APPID', 'mock_appid')

    # 业务配置
    LOW_STOCK_THRESHOLD = 10
    ORDER_EXPIRE_MINUTES = 30
