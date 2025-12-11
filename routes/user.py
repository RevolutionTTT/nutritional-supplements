from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from models.database import db
from models.models import Order

user_bp = Blueprint('user', __name__)

# ============================
# 用户个人信息页
# ============================
@user_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    # 渲染用户信息模板
    return render_template('user/profile.html', user=current_user)

# ============================
# 更新用户个人信息
# ============================
@user_bp.route('/profile', methods=['POST'])
@login_required
def update_profile():
    if request.is_json:
        data = request.get_json()
    else:
        # 强制要求 JSON 格式请求
        return jsonify({'message': 'Content-Type must be application/json'}), 415

    # 更新用户基本信息
    current_user.full_name = data.get('full_name', current_user.full_name)
    current_user.email = data.get('email', current_user.email)
    current_user.phone = data.get('phone', current_user.phone)
    current_user.address = data.get('address', current_user.address)

    # 可选更新密码
    new_password = data.get('new_password')
    if new_password:
        current_user.set_password(new_password)

    db.session.commit()
    return jsonify({'message': '个人信息更新成功', 'user': current_user.to_dict()})

# ============================
# 用户订单列表页
# ============================
@user_bp.route('/orders')
@login_required
def user_orders():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')

    # 构建查询条件
    query = Order.query.filter_by(user_id=current_user.id)
    if status != 'all':
        query = query.filter_by(status=status)

    # 分页查询订单
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    # 渲染模板并传入订单数据
    return render_template('user/orders.html', orders=orders, status=status)
