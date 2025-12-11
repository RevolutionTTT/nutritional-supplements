# models/database.py
# =============================================
# 数据库与安全相关扩展初始化模块
# =============================================

from flask_sqlalchemy import SQLAlchemy   # Flask 的 ORM，用于数据库操作
from flask_jwt_extended import JWTManager # JWT 管理，用于用户认证与授权
from flask_bcrypt import Bcrypt           # 密码哈希加密，用于存储安全密码

# =============================================
# 全局扩展实例
# =============================================
db = SQLAlchemy()   # 数据库操作实例，负责模型映射与查询
jwt = JWTManager()  # JWT实例，管理访问令牌及刷新机制
bcrypt = Bcrypt()   # 密码加密实例，用于哈希和验证密码

# =============================================
# 初始化函数
# 参数:
#   app: Flask 应用实例
# 功能:
#   将上述全局扩展与 Flask 应用绑定
# =============================================
def init_app(app):
    db.init_app(app)     # 绑定 SQLAlchemy 到 app
    jwt.init_app(app)    # 绑定 JWTManager 到 app
    bcrypt.init_app(app) # 绑定 Bcrypt 到 app
