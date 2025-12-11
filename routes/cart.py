from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from models.database import db
from models.models import CartItem, Product, Order, OrderItem

cart_bp = Blueprint('cart', __name__)


# ---------------------- 获取购物车页面 ----------------------
@cart_bp.route('/', methods=['GET'])
@login_required
def get_cart():
    # 查询当前用户所有购物车条目
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

    cart_data = []
    total_amount = 0

    # 逐项构造购物车展示数据
    for item in cart_items:
        subtotal = item.quantity * float(item.product.price)
        total_amount += subtotal

        cart_data.append({
            'id': item.id,
            'product_id': item.product.id,
            'product_name': item.product.name,
            'product_image': item.product.image_url,
            'product_price': float(item.product.price),
            'quantity': item.quantity,
            'subtotal': subtotal
        })

    return render_template('cart.html', cart_items=cart_data, total_amount=total_amount)


# ---------------------- 添加/更新购物车 ----------------------
@cart_bp.route('/add', methods=['POST'])
@login_required
def add_to_cart():
    # 接收 JSON 或表单
    data = request.get_json() if request.is_json else request.form
    if not data:
        msg = '请求数据为空'
        if request.is_json:
            return jsonify({'error': msg}), 400
        flash(msg, 'error')
        return redirect(request.referrer or url_for('cart.get_cart'))

    # 获取商品 ID 和数量
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))

    if not product_id:
        msg = '缺少商品信息'
        if request.is_json:
            return jsonify({'error': msg}), 400
        flash(msg, 'error')
        return redirect(request.referrer or url_for('cart.get_cart'))

    # 查询商品是否存在
    product = Product.query.get_or_404(product_id)

    # 库存检查
    if product.stock_quantity < quantity:
        msg = '库存不足'
        if request.is_json:
            return jsonify({'error': msg}), 400
        flash(msg, 'error')
        return redirect(request.referrer or url_for('cart.get_cart'))

    # 检查购物车是否已有此商品 → 更新 or 添加
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity = quantity
    else:
        cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)

    db.session.commit()

    msg = '已添加/更新购物车'
    if request.is_json:
        return jsonify({'message': msg})

    flash(msg, 'success')
    return redirect(request.referrer or url_for('cart.get_cart'))


# ---------------------- 删除购物车商品 ----------------------
@cart_bp.route('/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_cart_item(item_id):
    # 查找购物车条目
    cart_item = CartItem.query.get_or_404(item_id)

    # 权限检查
    if cart_item.user_id != current_user.id:
        return jsonify({'error': '无权操作'}), 403

    # 删除
    db.session.delete(cart_item)
    db.session.commit()

    return jsonify({'message': '已从购物车移除'})


# ---------------------- 结算购物车 → 生成订单 ----------------------
@cart_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    # 查询用户全部购物车条目
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

    # 购物车空
    if not cart_items:
        flash('购物车为空，无法结算', 'error')
        return redirect(url_for('cart.get_cart'))

    total_amount = 0

    # 遍历每一项，检查库存 + 累计金额
    for item in cart_items:
        if item.quantity > item.product.stock_quantity:
            flash(f"{item.product.name} 库存不足", 'error')
            return redirect(url_for('cart.get_cart'))

        total_amount += item.quantity * float(item.product.price)

    # 获取用户地址（若无则使用默认）
    user_address = current_user.address or "默认地址"

    # 创建订单
    order = Order(
        user_id=current_user.id,
        total_amount=total_amount,
        shipping_address=user_address,
        status='pending'  # 创建后等待支付
    )
    db.session.add(order)
    db.session.flush()  # 立刻生成 order.id，用来关联 order item

    # 写入订单项 + 扣库存 + 清空购物车
    for item in cart_items:
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.product.price
        ))
        # 扣减库存
        item.product.stock_quantity -= item.quantity
        # 删除购物车记录
        db.session.delete(item)

    db.session.commit()

    # 跳转到支付页面
    return redirect(url_for('payment.payment_page', order_id=order.id))
