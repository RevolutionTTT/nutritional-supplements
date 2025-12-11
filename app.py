from flask import Flask, render_template, jsonify
from flask_login import LoginManager, current_user
from config import Config
from models.database import db, init_app
from models.models import User, Category, Product
from utils.notifications import check_low_stock
from datetime import datetime

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(Config)
    app.last_stock_check = datetime.now()  # 记录上次库存检查时间

    # =========================
    # 初始化扩展
    # =========================
    init_app(app)

    # =========================
    # Flask-Login 配置
    # =========================
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # =========================
    # 注册蓝图
    # =========================
    from routes.auth import auth_bp
    from routes.products import products_bp
    from routes.orders import orders_bp
    from routes.cart import cart_bp
    from routes.admin import admin_bp
    from routes.user import user_bp
    from routes.reviews import reviews_bp
    from routes.payment import payment_bp
    from routes.announcement import announcement_bp
    from routes.nutrition import nutrition_bp
    from routes.rank import product_bp

    app.register_blueprint(product_bp)
    app.register_blueprint(nutrition_bp)
    app.register_blueprint(announcement_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(orders_bp, url_prefix='/orders')
    app.register_blueprint(cart_bp, url_prefix='/cart')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(reviews_bp, url_prefix='/api/reviews')
    app.register_blueprint(payment_bp, url_prefix='/payment')

    # =========================
    # 首页路由
    # =========================
    @app.route('/')
    def index():
        return render_template('index.html')

    # =========================
    # 健康检查接口
    # =========================
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': '营养补充剂销售系统运行正常',
            'user': current_user.to_dict() if current_user.is_authenticated else None
        })

    # =========================
    # 请求前库存检查（每天第一次请求触发）
    # =========================
    @app.before_request
    def check_stock_before_request():
        if not hasattr(app, 'last_stock_check'):
            app.last_stock_check = datetime.now()
        time_diff = datetime.now() - app.last_stock_check
        if time_diff.total_seconds() > 86400:  # 24小时
            check_low_stock()
            app.last_stock_check = datetime.now()

    # =========================
    # 创建数据库表和示例数据
    # =========================
    with app.app_context():
        db.create_all()
        create_sample_data()

    return app


def create_sample_data():
    """创建示例数据"""
    # 默认管理员
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@nutrition.com',
            full_name='系统管理员',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)

    # 示例分类
    if Category.query.count() == 0:
        categories = [
            Category(name='维生素', description='各种维生素补充剂'),
            Category(name='矿物质', description='钙、铁、锌等矿物质补充'),
            Category(name='蛋白粉', description='健身营养蛋白补充'),
            Category(name='氨基酸', description='必需氨基酸补充剂')
        ]
        db.session.add_all(categories)
        db.session.commit()

    # 示例产品
    if Product.query.count() == 0:
        vitamin_cat = Category.query.filter_by(name='维生素').first()
        mineral_cat = Category.query.filter_by(name='矿物质').first()
        protein_cat = Category.query.filter_by(name='蛋白粉').first()

        products = [
            Product(
                name='维生素C 1000mg',
                description='高效维生素C补充，增强免疫力，抗氧化，促进胶原蛋白合成',
                category_id=vitamin_cat.id,
                price=89.90,
                stock_quantity=100
            ),
            Product(
                name='钙镁锌片',
                description='复合矿物质补充，强健骨骼，维持神经肌肉正常功能',
                category_id=mineral_cat.id,
                price=129.00,
                stock_quantity=80
            ),
            Product(
                name='乳清蛋白粉',
                description='优质乳清蛋白，健身必备，快速补充蛋白质',
                category_id=protein_cat.id,
                price=299.00,
                stock_quantity=50
            )
        ]
        db.session.add_all(products)
        db.session.commit()


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
