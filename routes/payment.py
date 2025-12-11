from flask import Blueprint, render_template, jsonify, url_for
from flask_login import login_required, current_user
from models.database import db
from models.models import Order, User

payment_bp = Blueprint('payment', __name__)

# ===============================
# 支付页面：根据订单 ID 加载支付界面
# ===============================
@payment_bp.route('/<int:order_id>', methods=['GET'])
@login_required
def payment_page(order_id):
    # 查询当前用户的订单，不允许越权访问
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('payment/payment.html', order=order)

# ===============================
# 支付订单逻辑
# ===============================
@payment_bp.route('/pay/<int:order_id>', methods=['POST'])
@login_required
def pay_order(order_id):
    # 查询订单并验证用户权限
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    user = db.session.query(User).filter_by(id=current_user.id).first()

    # 若订单已支付，直接返回错误信息
    if order.status == 'paid':
        return jsonify({'success': False, 'message': '订单已支付', 'balance': float(user.balance)})

    # 检查用户余额是否足够
    if user.balance < float(order.total_amount):
        return jsonify({'success': False, 'message': '余额不足', 'balance': float(user.balance)})

    # 扣款并标记订单为已支付
    user.balance -= float(order.total_amount)
    order.status = 'paid'

    try:
        # 提交事务
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'支付成功，扣除 ¥{order.total_amount}',
            'balance': float(user.balance),
            'redirect': url_for('orders.get_order', order_id=order.id)
        })
    except Exception as e:
        # 出错则回滚事务
        db.session.rollback()
        return jsonify({'success': False, 'message': f'支付失败: {str(e)}', 'balance': float(user.balance)})
