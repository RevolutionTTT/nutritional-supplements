from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from models.database import db
from models.models import Order, OrderItem, CartItem, Product, Review

# 创建订单蓝图，管理所有订单相关接口
orders_bp = Blueprint('orders', __name__, url_prefix='/orders')


# ===============================
# 订单列表
# ===============================
@orders_bp.route('/', methods=['GET'])
@login_required
def get_orders():
    # 查询当前用户所有订单，按创建时间倒序排列
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()

    # 如果是 JSON 请求，则返回订单字典数据
    if request.is_json:
        return jsonify([order.to_dict() for order in orders])
    else:
        # 非 JSON 请求，将订单条目转换成字典提供给模板
        for order in orders:
            order.order_items_json = [item.to_dict() for item in order.order_items]

        # 渲染订单列表页面
        return render_template('orders.html', orders=orders)


# ===============================
# 订单详情
# ===============================
@orders_bp.route('/<int:order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    # 查询订单，不存在返回 404
    order = Order.query.get_or_404(order_id)

    # 权限校验：仅订单所有者或管理员可访问
    if order.user_id != current_user.id and not getattr(current_user, "is_admin", False):
        if request.is_json:
            return jsonify({'error': '无权访问'}), 403
        else:
            flash('无权访问', 'error')
            return redirect(url_for('orders.get_orders'))

    # JSON 请求返回序列化后的订单数据
    if request.is_json:
        return jsonify(order.to_dict())
    else:
        # 提供订单商品信息给模板
        order.order_items_json = [item.to_dict() for item in order.order_items]
        return render_template('order_detail.html', order=order)


# ===============================
# 创建订单
# ===============================
@orders_bp.route('/', methods=['POST'])
@login_required
def create_order():
    # 获取表单或 JSON 数据
    data = request.get_json() or request.form

    # 获取当前用户购物车中所有商品
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        msg = '购物车为空'
        if request.is_json:
            return jsonify({'error': msg}), 400
        else:
            flash(msg, 'error')
            return redirect(url_for('cart.get_cart'))

    total_amount = 0
    order_items_data = []

    # 遍历购物车，检查库存并计算金额
    for item in cart_items:
        product = Product.query.get(item.product_id)

        # 库存不足校验
        if product.stock_quantity < item.quantity:
            msg = f'产品 {product.name} 库存不足'
            if request.is_json:
                return jsonify({'error': msg}), 400
            else:
                flash(msg, 'error')
                return redirect(url_for('cart.get_cart'))

        # 计算该商品的总价
        item_total = float(product.price) * item.quantity
        total_amount += item_total

        # 暂存订单项数据
        order_items_data.append({
            'product': product,
            'quantity': item.quantity,
            'unit_price': float(product.price)
        })

    # 创建订单
    order = Order(
        user_id=current_user.id,
        total_amount=total_amount,
        shipping_address=data.get('shipping_address', current_user.address),
        payment_method=data.get('payment_method', '在线支付'),
        status='pending'
    )
    db.session.add(order)
    db.session.flush()  # 提前获取订单 ID

    # 创建订单项并扣减库存
    for item in order_items_data:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item['product'].id,
            quantity=item['quantity'],
            unit_price=item['unit_price']
        )
        db.session.add(order_item)
        item['product'].stock_quantity -= item['quantity']

    # 清空购物车
    CartItem.query.filter_by(user_id=current_user.id).delete()

    # 提交事务
    db.session.commit()

    # 返回 JSON 或页面跳转
    if request.is_json:
        return jsonify({'message': '订单创建成功', 'order_id': order.id, 'order': order.to_dict()}), 201
    else:
        flash('订单创建成功', 'success')
        return redirect(url_for('orders.get_order', order_id=order.id))


# ===============================
# 取消订单
# ===============================
@orders_bp.route('/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    # 查询订单
    order = Order.query.get_or_404(order_id)

    # 权限校验
    if order.user_id != current_user.id and not getattr(current_user, "is_admin", False):
        if request.is_json:
            return jsonify({'error': '无权操作'}), 403
        else:
            flash('无权操作', 'error')
            return redirect(url_for('orders.get_orders'))

    # 允许取消的订单状态校验
    if order.status not in ['pending', 'confirmed']:
        msg = '订单无法取消'
        if request.is_json:
            return jsonify({'error': msg}), 400
        else:
            flash(msg, 'error')
            return redirect(url_for('orders.get_order', order_id=order_id))

    # 取消订单后还原库存
    for item in order.order_items:
        product = Product.query.get(item.product_id)
        product.stock_quantity += item.quantity

    # 更新订单状态
    order.status = 'cancelled'
    db.session.commit()

    # 返回结果
    if request.is_json:
        return jsonify({'message': '订单已取消'})
    else:
        flash('订单已取消', 'success')
        return redirect(url_for('orders.get_order', order_id=order_id))


# ===============================
# 提交评论
# ===============================
@orders_bp.route('/<int:order_id>/review', methods=['POST'])
@login_required
def submit_review(order_id):
    # 查询订单
    order = Order.query.get_or_404(order_id)

    # 评论权限校验
    if order.user_id != current_user.id:
        return jsonify({'error': '无权评论'}), 403

    # 解析 JSON 数据
    data = request.get_json()
    product_id = int(data.get('product_id'))
    rating = int(data.get('rating', 5))
    title = data.get('title', '')
    content = data.get('content', '')

    # 参数合法性校验
    if not product_id or not (1 <= rating <= 5):
        return jsonify({'error': '参数不合法'}), 400

    # 校验用户是否购买过该商品
    order_item = next((item for item in order.order_items if item.product_id == product_id), None)
    if not order_item:
        return jsonify({'error': '订单中没有该商品'}), 400

    # 校验是否已评论过
    existing_review = Review.query.filter_by(
        user_id=current_user.id,
        order_id=order.id,
        product_id=product_id
    ).first()
    if existing_review:
        return jsonify({'error': '您已评论过该商品'}), 400

    # 创建评论
    review = Review(
        user_id=current_user.id,
        order_id=order.id,
        product_id=product_id,
        rating=rating,
        title=title,
        content=content,
        is_verified=True
    )
    db.session.add(review)
    db.session.commit()

    return jsonify({'message': '评论提交成功', 'review_id': review.id})


# ===============================
# 确认收货
# ===============================
@orders_bp.route('/<int:order_id>/confirm', methods=['POST'])
@login_required
def confirm_order(order_id):
    # 查询订单
    order = Order.query.get_or_404(order_id)

    # 权限校验
    if order.user_id != current_user.id and not getattr(current_user, "is_admin", False):
        if request.is_json:
            return jsonify({'error': '无权操作'}), 403
        else:
            flash('无权操作', 'error')
            return redirect(url_for('orders.get_orders'))

    # 仅已发货订单可确认收货
    if order.status != 'shipped':
        msg = '订单无法确认收货'
        if request.is_json:
            return jsonify({'error': msg}), 400
        else:
            flash(msg, 'error')
            return redirect(url_for('orders.get_order', order_id=order_id))

    # 更新订单状态为“已收货”
    order.status = 'delivered'
    db.session.commit()

    # 返回结果
    if request.is_json:
        return jsonify({'message': '已确认收货'})
    else:
        flash('已确认收货', 'success')
        return redirect(url_for('orders.get_order', order_id=order_id))


# ===============================
# 申请退款
# ===============================
@orders_bp.route('/<int:order_id>/refund', methods=['POST'])
@login_required
def request_refund(order_id):
    # 查询订单
    order = Order.query.get_or_404(order_id)

    # 权限校验
    if order.user_id != current_user.id and not getattr(current_user, "is_admin", False):
        msg = '无权操作'
        if request.is_json:
            return jsonify({'error': msg}), 403
        else:
            flash(msg, 'error')
            return redirect(url_for('orders.get_orders'))

    # 仅已支付或已发货订单可申请退款
    if order.status not in ['paid', 'shipped']:
        msg = '订单无法申请退款'
        if request.is_json:
            return jsonify({'error': msg}), 400
        else:
            flash(msg, 'error')
            return redirect(url_for('orders.get_order', order_id=order_id))

    # 更新订单状态为退款申请中
    order.status = 'refund_requested'
    db.session.commit()

    msg = '退款申请已提交'

    # 返回结果
    if request.is_json:
        return jsonify({'message': msg})
    else:
        flash(msg, 'success')
        return redirect(url_for('orders.get_order', order_id=order_id))
