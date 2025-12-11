# routes/reviews.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.database import db
from models.models import Review, Order, OrderItem
from datetime import datetime

# 定义全局时间字段（模型中一般不直接定义在路由里，此处仅作说明）
created_at = db.Column(db.DateTime, default=datetime.utcnow)
updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

reviews_bp = Blueprint('reviews', __name__)

# ============================
# 获取商品评价列表（带分页）
# ============================
@reviews_bp.route('/products/<int:product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id):
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 2, type=int)

    # 查询指定商品的评价，并分页
    reviews = Review.query.filter_by(product_id=product_id).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # 计算平均评分
    avg_rating = db.session.query(db.func.avg(Review.rating)).filter_by(
        product_id=product_id
    ).scalar() or 0

    # 统计评分分布
    rating_distribution = db.session.query(
        Review.rating, db.func.count(Review.id)
    ).filter_by(product_id=product_id).group_by(Review.rating).all()

    return jsonify({
        'reviews': [r.to_dict() for r in reviews.items],
        'average_rating': round(float(avg_rating), 1),
        'total_reviews': reviews.total,
        'rating_distribution': dict(rating_distribution),
        'pagination': {
            'page': page,
            'pages': reviews.pages,
            'total': reviews.total
        }
    })


# ============================
# 创建新评价
# ============================
@reviews_bp.route('/', methods=['POST'])
@login_required
def create_review():
    data = request.get_json()

    # 验证用户是否购买过该商品（只有已收货订单可评价）
    order_item = OrderItem.query.join(Order).filter(
        OrderItem.product_id == data['product_id'],
        Order.user_id == current_user.id,
        Order.status == 'delivered'
    ).first()

    if not order_item:
        return jsonify({'error': '只有购买过该商品才能评价'}), 400

    # 检查是否已评价过该订单商品
    existing_review = Review.query.filter_by(
        user_id=current_user.id,
        product_id=data['product_id'],
        order_id=order_item.order_id
    ).first()

    if existing_review:
        return jsonify({'error': '您已经评价过该商品'}), 400

    # 创建评价记录
    review = Review(
        user_id=current_user.id,
        product_id=data['product_id'],
        order_id=order_item.order_id,
        rating=data['rating'],
        title=data.get('title', ''),
        content=data.get('content', ''),
        is_verified=True
    )

    db.session.add(review)
    db.session.commit()

    return jsonify({'message': '评价提交成功', 'review': review.to_dict()}), 201


# ============================
# 更新评价
# ============================
@reviews_bp.route('/<int:review_id>', methods=['PUT'])
@login_required
def update_review(review_id):
    review = Review.query.get_or_404(review_id)

    # 权限校验：仅作者可修改
    if review.user_id != current_user.id:
        return jsonify({'error': '无权修改该评价'}), 403

    data = request.get_json()
    review.rating = data.get('rating', review.rating)
    review.title = data.get('title', review.title)
    review.content = data.get('content', review.content)
    review.updated_at = datetime.utcnow()  # 更新时间

    db.session.commit()

    return jsonify({'message': '评价更新成功', 'review': review.to_dict()})


# ============================
# 删除评价
# ============================
@reviews_bp.route('/<int:review_id>', methods=['DELETE'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)

    # 权限校验：作者或管理员可删除
    if review.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': '无权删除该评价'}), 403

    db.session.delete(review)
    db.session.commit()

    return jsonify({'message': '评价删除成功'})
