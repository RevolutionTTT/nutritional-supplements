from flask import Blueprint, render_template
from models.models import Product, OrderItem, Review
from models.database import db
from sqlalchemy import func, desc

product_bp = Blueprint('product', __name__, url_prefix='/products')

# ============================
# 热门排行榜
# ============================
@product_bp.route('/ranking')
def product_ranking():
    # ----------------------------
    # 按销量统计：计算每个商品的总销量
    # ----------------------------
    sales_subquery = (
        db.session.query(
            OrderItem.product_id,
            func.sum(OrderItem.quantity).label('total_sales')  # 总销量
        )
        .group_by(OrderItem.product_id)
        .subquery()
    )

    # ----------------------------
    # 按评分统计：计算每个商品的平均评分
    # ----------------------------
    rating_subquery = (
        db.session.query(
            Review.product_id,
            func.avg(Review.rating).label('avg_rating')  # 平均评分
        )
        .group_by(Review.product_id)
        .subquery()
    )

    # ----------------------------
    # 关联 Product 表、销量子查询、评分子查询
    # 并按销量和评分倒序排序，取前10
    # ----------------------------
    ranking_query = (
        db.session.query(
            Product,
            func.coalesce(sales_subquery.c.total_sales, 0).label('sales'),   # 如果销量为空，默认0
            func.coalesce(rating_subquery.c.avg_rating, 0).label('rating')   # 如果评分为空，默认0
        )
        .outerjoin(sales_subquery, Product.id == sales_subquery.c.product_id)
        .outerjoin(rating_subquery, Product.id == rating_subquery.c.product_id)
        .filter(Product.is_active == True)  # 只显示上架商品
        .order_by(desc('sales'), desc('rating'))  # 先按销量，再按评分
        .limit(10)  # 取前10名
        .all()
    )

    # 渲染模板，传入排行榜数据
    return render_template('rank.html', ranking=ranking_query)
