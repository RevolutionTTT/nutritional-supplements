import os
import uuid
from decimal import Decimal
from io import BytesIO
import base64
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename
from sqlalchemy import func
from matplotlib import rcParams
from flask import request, redirect, url_for, flash, jsonify, Blueprint, render_template
from flask_login import current_user, login_required

"""
后台管理蓝图
负责：用户管理、商品管理、订单、评价、公告、文章等后台功能
"""
from models.models import (
    db,
    User,
    Product,
    Category,
    Order,
    OrderItem,
    Review
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ===============================
# 文件上传配置
# ===============================

# 产品图片上传路径：项目/static/images/products/
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'images/products')

# 允许上传的文件格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 若目录不存在则自动创建
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """判断文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    """保存图片到服务器，并返回供数据库保存的相对路径"""
    if file and allowed_file(file.filename):
        # 使用 UUID 防止重名覆盖
        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)
        # 返回相对路径（用于 HTML 显示）
        return f"images/products/{filename}"
    return None


# ===============================
# 权限检查（所有 admin 路由必须是管理员）
# ===============================
@admin_bp.before_request
def check_admin():
    """非管理员用户禁止访问后台"""
    if not current_user.is_admin:
        flash('需要管理员权限', 'error')
        return redirect(url_for('main.index'))


# ===============================
# 后台首页 Dashboard
# ===============================
@admin_bp.route('/')
@login_required
def dashboard():
    """后台首页统计数据"""
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()

    # 最近 10 条订单
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_products=total_products,
                           total_orders=total_orders,
                           recent_orders=recent_orders)


# ===============================
# 用户管理
# ===============================
@admin_bp.route('/users', methods=['GET','POST'])
@login_required
def manage_users():
    """用户列表 + 添加用户"""
    if request.method == 'POST':
        action = request.form.get('action')

        # 添加用户
        if action == 'add':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            full_name = request.form.get('full_name')
            phone = request.form.get('phone')
            address = request.form.get('address')
            is_admin = request.form.get('is_admin') == '1'

            # 检查用户名/邮箱是否重复
            if User.query.filter((User.username == username) | (User.email == email)).first():
                flash('用户名或邮箱已存在','danger')
            else:
                new_user = User(
                    username=username,
                    email=email,
                    full_name=full_name,
                    phone=phone,
                    address=address,
                    is_admin=is_admin
                )
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                flash(f'用户 {username} 添加成功','success')

            return redirect(url_for('admin.manage_users'))

    # 查询所有用户
    users = User.query.all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/<int:user_id>/update', methods=['POST'])
@login_required
def update_user(user_id):
    """更新用户信息"""
    user = User.query.get_or_404(user_id)
    data = request.form

    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    user.full_name = data.get('full_name', user.full_name)
    user.phone = data.get('phone', user.phone)
    user.address = data.get('address', user.address)
    user.is_admin = data.get('is_admin') == '1'

    db.session.commit()
    flash('用户信息更新成功', 'success')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """删除用户（管理员禁止删除）"""
    user = User.query.get_or_404(user_id)

    if user.is_admin:
        return jsonify({'success': False, 'message': '不能删除管理员'}), 400

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True, 'message': '用户删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ===============================
# 产品管理
# ===============================
@admin_bp.route('/products')
@login_required
def manage_products():
    """展示产品列表 + 分类"""
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('admin/products.html', products=products, categories=categories)


@admin_bp.route('/products/create', methods=['POST'])
@login_required
def create_product():
    """创建产品"""
    data = request.form
    image_file = request.files.get('image')

    # 保存图片
    image_path = save_image(image_file)

    product = Product(
        name=data.get('name'),
        description=data.get('description'),
        category_id=int(data.get('category_id')),
        price=float(data.get('price', 0)),
        stock_quantity=int(data.get('stock_quantity', 0)),
        image_url=image_path,
        is_active=True
    )
    db.session.add(product)
    db.session.commit()
    flash('产品创建成功', 'success')
    return redirect(url_for('admin.manage_products'))


@admin_bp.route('/products/<int:product_id>/update', methods=['POST'])
@login_required
def update_product(product_id):
    """更新产品信息"""
    product = Product.query.get_or_404(product_id)
    data = request.form

    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.category_id = int(data.get('category_id', product.category_id))
    product.price = float(data.get('price', product.price))
    product.stock_quantity = int(data.get('stock_quantity', product.stock_quantity))
    product.is_active = data.get('is_active') == '1'

    # 新图覆盖旧图
    image_file = request.files.get('image')
    image_path = save_image(image_file)
    if image_path:
        product.image_url = image_path

    db.session.commit()
    flash('产品更新成功', 'success')
    return redirect(url_for('admin.manage_products'))


@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    """删除产品"""
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('产品已删除', 'success')
    return redirect(url_for('admin.manage_products'))


# ===============================
# 订单管理
# ===============================
@admin_bp.route('/orders')
@login_required
def manage_orders():
    """订单列表"""
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)


@admin_bp.route('/orders/<int:order_id>/update_status', methods=['POST'])
@login_required
def update_order_status(order_id):
    """订单状态流转：校验合法流转并执行退款逻辑"""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')

    # 定义合法状态流转
    valid_transitions = {
        'pending': ['paid','cancelled'],
        'paid': ['shipped','refund_requested'],
        'shipped': ['delivered','refund_requested'],
        'refund_requested': ['refunded'],
        'delivered': [],
        'refunded': [],
        'cancelled': []
    }

    if new_status not in valid_transitions.get(order.status, []):
        flash(f'无法从 {order.status} 变为 {new_status}', 'error')
        return redirect(url_for('admin.manage_orders'))

    try:
        # 若进入 refunded 状态，则执行退款
        if new_status == 'refunded' and order.status != 'refunded':
            order.user.balance = Decimal(order.user.balance) + Decimal(order.total_amount)

        order.status = new_status
        db.session.commit()
        flash(f'订单状态已更新为 {new_status}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'操作失败: {str(e)}', 'error')

    return redirect(url_for('admin.manage_orders'))


@admin_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """订单详情页"""
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)


@admin_bp.route('/orders/<int:order_id>/approve_refund', methods=['POST'])
@login_required
def approve_refund(order_id):
    """管理员审核退款"""
    if not current_user.is_admin:
        flash('需要管理员权限', 'error')
        return redirect(url_for('admin.dashboard'))

    order = Order.query.get_or_404(order_id)

    if order.status != 'refund_requested':
        flash('该订单没有退款申请', 'error')
        return redirect(url_for('admin.manage_orders'))

    # 执行退款
    order.user.balance = Decimal(order.user.balance) + Decimal(order.total_amount)
    order.status = 'refunded'

    try:
        db.session.commit()
        flash(f'订单 {order.id} 退款成功，用户余额已更新', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'退款失败: {str(e)}', 'error')

    return redirect(url_for('admin.manage_orders'))


# ===============================
# 评价管理
# ===============================
@admin_bp.route('/reviews')
@login_required
def manage_reviews():
    """评价列表"""
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('admin/reviews.html', reviews=reviews)


@admin_bp.route('/reviews/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    """删除用户评价"""
    review = Review.query.get_or_404(review_id)
    try:
        db.session.delete(review)
        db.session.commit()
        flash('评价已删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'error')

    return redirect(url_for('admin.manage_reviews'))



from models.models import Announcement

# ===============================
# 公告管理
# ===============================
@admin_bp.route('/announcement', methods=['GET', 'POST'])
@login_required
def manage_announcement():
    """管理网站公告（仅允许单条）"""
    if not current_user.is_admin:
        flash('需要管理员权限', 'error')
        return redirect(url_for('admin.dashboard'))

    # 当前公告（系统只保留一条）
    announcement = Announcement.query.first()

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')

        if not title or not content:
            flash('标题和内容不能为空', 'error')
        else:
            if announcement:
                # 更新公告
                announcement.title = title
                announcement.content = content
                flash('公告已更新', 'success')
            else:
                # 创建公告
                new_announcement = Announcement(title=title, content=content)
                db.session.add(new_announcement)
                flash('公告已发布', 'success')

            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f'操作失败: {str(e)}', 'error')

        return redirect(url_for('admin.manage_announcement'))

    return render_template('admin/announcement.html', announcement=announcement)


from models.models import Article

# ===============================
# 营养百科（科普文章）管理
# ===============================
@admin_bp.route('/articles')
@login_required
def article_list():
    """显示文章列表"""
    articles = Article.query.order_by(Article.created_at.desc()).all()
    return render_template('admin/articles/list.html', articles=articles)

@admin_bp.route('/articles/create', methods=['GET', 'POST'])
@login_required
def article_create():
    """
    创建科普文章
    GET：返回创建页面
    POST：接收表单并写入数据库
    """
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')

        # 基础校验：标题与内容不能为空
        if not title or not content:
            flash('标题和内容不能为空', 'error')
            return redirect(url_for('admin.article_create'))

        # 创建文章实例并保存
        new_article = Article(title=title, content=content)
        db.session.add(new_article)
        db.session.commit()

        flash('科普文章创建成功', 'success')
        return redirect(url_for('admin.article_list'))

    return render_template('admin/articles/create.html')


@admin_bp.route('/articles/<int:article_id>')
@login_required
def article_detail(article_id):
    """
    文章详情页
    根据文章 ID 查询并显示全文
    """
    article = Article.query.get_or_404(article_id)
    return render_template('admin/articles/detail.html', article=article)


@admin_bp.route('/articles/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
def article_edit(article_id):
    """
    编辑文章
    GET：加载文章内容
    POST：提交更新后的数据
    """
    article = Article.query.get_or_404(article_id)

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')

        # 基础校验
        if not title or not content:
            flash('标题和内容不能为空', 'error')
            return redirect(url_for('admin.article_edit', article_id=article_id))

        # 更新数据并保存
        article.title = title
        article.content = content
        db.session.commit()

        flash('文章已更新', 'success')
        return redirect(url_for('admin.article_detail', article_id=article.id))

    return render_template('admin/articles/edit.html', article=article)


@admin_bp.route('/articles/<int:article_id>/delete', methods=['POST'])
@login_required
def article_delete(article_id):
    """
    删除文章
    操作包含事务处理：失败则回滚
    """
    article = Article.query.get_or_404(article_id)

    try:
        db.session.delete(article)
        db.session.commit()
        flash('文章已删除', 'success')
    except Exception as e:
        db.session.rollback()  # 删除失败必须回滚事务
        flash(f'删除失败: {str(e)}', 'error')

    return redirect(url_for('admin.article_list'))


@admin_bp.route('/dashboard/stats')
@login_required
def dashboard_stats():
    """
    后台统计面板
    - 每日订单数量与销售额（柱状 + 折线）
    - 按品类销售额分布（饼图）
    图像使用内存缓冲，并转为 Base64 供 HTML 显示
    """

    # 解决中文字体和负号显示问题
    rcParams['font.sans-serif'] = ['SimHei']
    rcParams['axes.unicode_minus'] = False

    # ===================== 每日订单销量与金额 =====================
    # 联结 Order 与 OrderItem，按日期统计销量与销售额
    daily_sales = db.session.query(
        func.date(Order.created_at).label('day'),
        func.sum(OrderItem.quantity).label('total_quantity'),
        func.sum(OrderItem.quantity * OrderItem.unit_price).label('total_sales')
    ).join(Order, OrderItem.order_id == Order.id) \
     .group_by(func.date(Order.created_at)) \
     .order_by(func.date(Order.created_at)) \
     .all()

    # 转换为可绘图格式
    days = [row.day.strftime('%Y-%m-%d') for row in daily_sales] if daily_sales else []
    quantities = [row.total_quantity for row in daily_sales] if daily_sales else []
    sales = [float(row.total_sales) for row in daily_sales] if daily_sales else []

    # 绘制柱状图 + 折线图（双轴）
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    ax1.bar(days, quantities, color='skyblue', label='订单数量')
    ax1.set_xlabel('日期')
    ax1.set_ylabel('订单数量', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.set_xticks(range(len(days)))
    ax1.set_xticklabels(days, rotation=45, ha='right')

    ax2 = ax1.twinx()
    ax2.plot(days, sales, color='orange', marker='o', label='销售额')
    ax2.set_ylabel('销售额（元）', color='orange')
    ax2.tick_params(axis='y', labelcolor='orange')

    # 防止图像元素被遮挡
    fig1.tight_layout()
    plt.title('每日订单数量与销售额统计')

    # 转为 Base64 方便前端展示
    buf1 = BytesIO()
    plt.savefig(buf1, format='png', bbox_inches='tight')
    plt.close(fig1)
    buf1.seek(0)
    daily_plot = base64.b64encode(buf1.getvalue()).decode()

    # ===================== 按品类销售额饼图 =====================
    category_sales = db.session.query(
        Category.name,
        func.sum(OrderItem.quantity * OrderItem.unit_price).label('total_sales')
    ).join(Product, Product.category_id == Category.id) \
     .join(OrderItem, OrderItem.product_id == Product.id) \
     .group_by(Category.id).all()

    labels = [row.name for row in category_sales]
    values = [float(row.total_sales) for row in category_sales]

    fig2, ax3 = plt.subplots(figsize=(8, 8))
    ax3.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
    ax3.axis('equal')  # 保持饼图为正圆
    plt.title('按品类销量分布')

    buf2 = BytesIO()
    plt.savefig(buf2, format='png', bbox_inches='tight')
    plt.close(fig2)
    buf2.seek(0)
    category_plot = base64.b64encode(buf2.getvalue()).decode()

    # 返回模板，并携带两张图的 Base64 字符串
    return render_template(
        'admin/dashboard_stats.html',
        daily_plot=daily_plot,
        category_plot=category_plot
    )
