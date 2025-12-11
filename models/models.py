# models/models.py
# =============================================
# 数据库模型定义模块
# 包含用户、商品、订单、购物车、评价等核心表
# =============================================

from .database import db
from datetime import datetime
from flask_login import UserMixin

# =============================================
# 用户模型
# =============================================
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)                     # 用户ID
    username = db.Column(db.String(50), unique=True, nullable=False) # 登录用户名
    email = db.Column(db.String(100), unique=True, nullable=False)   # 邮箱
    password_hash = db.Column(db.String(255), nullable=False)        # 密码哈希
    balance = db.Column(db.Float, default=1000)                      # 用户余额
    full_name = db.Column(db.String(100))                             # 用户全名
    phone = db.Column(db.String(20))                                  # 电话
    address = db.Column(db.Text)                                      # 收货地址
    is_admin = db.Column(db.Boolean, default=False)                  # 是否为管理员
    created_at = db.Column(db.DateTime, default=datetime.now)        # 创建时间

    # 关系映射
    orders = db.relationship('Order', backref='user', lazy=True, cascade='all, delete-orphan')  # 用户订单
    cart_items = db.relationship('CartItem', backref='user', lazy=True, cascade='all, delete-orphan')  # 购物车商品
    # reviews 通过 Review.user 的 backref 自动生成

    # 设置密码（明文存储，不推荐生产使用）
    def set_password(self, password):
        self.password_hash = password

    # 验证密码
    def check_password(self, password):
        return self.password_hash == password

    # 转换为字典（用于 JSON 返回）
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_admin': self.is_admin
        }

# =============================================
# 商品分类模型
# =============================================
class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)             # 分类ID
    name = db.Column(db.String(100), nullable=False)        # 分类名称
    description = db.Column(db.Text)                        # 分类描述
    image_url = db.Column(db.String(500))                   # 分类图片URL
    created_at = db.Column(db.DateTime, default=datetime.now)  # 创建时间

    products = db.relationship('Product', backref='category', lazy=True)  # 分类下的产品

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'product_count': len(self.products)  # 该分类下产品数量
        }

# =============================================
# 商品模型
# =============================================
class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)             # 商品ID
    name = db.Column(db.String(200), nullable=False)        # 商品名称
    description = db.Column(db.Text)                        # 商品描述
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))  # 分类ID
    price = db.Column(db.Numeric(10,2), nullable=False)     # 单价
    stock_quantity = db.Column(db.Integer, nullable=False)  # 库存数量
    image_url = db.Column(db.String(500))                   # 商品图片URL
    is_active = db.Column(db.Boolean, default=True)         # 是否上架
    created_at = db.Column(db.DateTime, default=datetime.now)  # 创建时间

    order_items = db.relationship('OrderItem', backref='product', lazy=True, cascade='all, delete-orphan')  # 订单项
    cart_items = db.relationship('CartItem', backref='product', lazy=True, cascade='all, delete-orphan')   # 购物车项
    # reviews 通过 Review.product 的 backref 自动生成

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'price': float(self.price),
            'stock_quantity': self.stock_quantity,
            'image_url': self.image_url,
            'is_active': self.is_active
        }

# =============================================
# 订单模型
# =============================================
class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)               # 订单ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)  # 用户ID
    total_amount = db.Column(db.Numeric(10,2), nullable=False)  # 总金额
    status = db.Column(db.String(20), default='pending')       # 订单状态: pending/paid/cancelled
    shipping_address = db.Column(db.Text, nullable=False)      # 收货地址
    payment_method = db.Column(db.String(50))                  # 支付方式
    created_at = db.Column(db.DateTime, default=datetime.now)  # 创建时间

    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')  # 订单项列表

    @property
    def total_price(self):
        """计算订单总价"""
        return float(sum(item.unit_price * item.quantity for item in self.order_items))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username,
            'total_amount': float(self.total_amount),
            'status': self.status,
            'shipping_address': self.shipping_address,
            'payment_method': self.payment_method,
            'created_at': self.created_at.isoformat(),
            'items': [item.to_dict() for item in self.order_items]
        }

# =============================================
# 订单项模型
# =============================================
class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)               # 订单项ID
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)  # 所属订单ID
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)  # 商品ID
    quantity = db.Column(db.Integer, nullable=False)           # 数量
    unit_price = db.Column(db.Numeric(10,2), nullable=False)  # 单价

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'total_price': float(self.unit_price * self.quantity)
        }


# =============================================
# 购物车项模型
# =============================================
class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)                     # 购物车项ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)  # 用户ID
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)  # 商品ID
    quantity = db.Column(db.Integer, nullable=False, default=1)      # 商品数量
    added_at = db.Column(db.DateTime, default=datetime.now)          # 添加时间

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'product_name': self.product.name,
            'product_price': float(self.product.price),
            'product_image': self.product.image_url,
            'quantity': self.quantity,
            'subtotal': float(self.product.price * self.quantity)
        }

# =============================================
# 商品评价模型
# =============================================
class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)                     # 评价ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)  # 用户ID
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)  # 商品ID
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)    # 订单ID
    rating = db.Column(db.Integer, nullable=False)                   # 评分（1-5）
    title = db.Column(db.String(200))                                # 标题
    content = db.Column(db.Text)                                      # 内容
    is_verified = db.Column(db.Boolean, default=False)               # 是否为已验证购买
    created_at = db.Column(db.DateTime, default=datetime.now)        # 创建时间
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 更新时间

    # 关系映射
    user = db.relationship('User', backref=db.backref('reviews', lazy=True, cascade='all, delete-orphan'))
    product = db.relationship('Product', backref=db.backref('reviews', lazy=True, cascade='all, delete-orphan'))
    order = db.relationship('Order', backref=db.backref('reviews', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name or self.user.username,
            'product_id': self.product_id,
            'rating': self.rating,
            'title': self.title,
            'content': self.content,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat()
        }

# =============================================
# 系统公告模型
# =============================================
class Announcement(db.Model):
    __tablename__ = 'announcements'

    id = db.Column(db.Integer, primary_key=True)       # 公告ID
    title = db.Column(db.String(200), nullable=False) # 公告标题
    content = db.Column(db.Text, nullable=False)      # 公告内容
    created_at = db.Column(db.DateTime, default=datetime.now)  # 创建时间

# =============================================
# 文章/博客模型
# =============================================
class Article(db.Model):
    __tablename__ = "articles"

    id = db.Column(db.Integer, primary_key=True)                  # 文章ID
    title = db.Column(db.String(255), nullable=False)             # 文章标题
    content = db.Column(db.Text, nullable=False)                  # 文章内容
    created_at = db.Column(db.DateTime, default=db.func.now())    # 创建时间
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())  # 更新时间

