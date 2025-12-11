from flask import Blueprint, request, jsonify, render_template
from models.models import Product, Category, Review

products_bp = Blueprint('products', __name__)

# ===============================
# 获取商品列表，支持分类筛选和搜索
# ===============================
@products_bp.route('/', methods=['GET'])
def get_products():
    category_id = request.args.get('category_id')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)

    # 构建查询条件：只显示上架商品
    query = Product.query.filter_by(is_active=True)
    if category_id and category_id != 'all':
        query = query.filter_by(category_id=category_id)
    if search:
        query = query.filter(Product.name.like(f'%{search}%'))

    # 分页查询
    products = query.paginate(page=page, per_page=per_page, error_out=False)
    categories = Category.query.all()

    # 根据请求格式返回 JSON 或渲染模板
    if request.args.get('format') == 'json':
        return jsonify({
            'products': [p.to_dict() for p in products.items],
            'categories': [c.to_dict() for c in categories],
            'total': products.total,
            'pages': products.pages,
            'current_page': page
        })
    else:
        return render_template(
            'products.html',
            products=products.items,
            categories=categories,
            pagination=products
        )

# ===============================
# 获取单个商品详情及其已验证评论
# ===============================
@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    # 查询商品
    product = Product.query.get_or_404(product_id)

    # 查询该商品已验证评论，按创建时间倒序
    reviews = Review.query.filter_by(product_id=product.id, is_verified=True).order_by(Review.created_at.desc()).all()
    reviews_data = [{
        'user_name': r.user.full_name or r.user.username,
        'rating': r.rating,
        'title': r.title,
        'content': r.content,
        'created_at': r.created_at.strftime('%Y-%m-%d %H:%M')
    } for r in reviews]

    # 根据请求格式返回 JSON 或渲染模板
    if request.args.get('format') == 'json':
        return jsonify({
            'product': product.to_dict(),
            'reviews': reviews_data
        })
    else:
        return render_template('product_detail.html', product=product, reviews=reviews_data)

# ===============================
# 获取商品分类列表
# ===============================
@products_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([c.to_dict() for c in categories])

# ===============================
# 获取商品评论分页接口
# ===============================
@products_bp.route('/<int:product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id):
    page = request.args.get('page', 1, type=int)
    per_page = 5  # 每页显示5条评论
    reviews_query = Review.query.filter_by(product_id=product_id).order_by(Review.created_at.desc())
    pagination = reviews_query.paginate(page=page, per_page=per_page, error_out=False)
    reviews = [r.to_dict() for r in pagination.items]
    return jsonify({'reviews': reviews})
