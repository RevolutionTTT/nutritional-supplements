from flask import Blueprint, render_template
from flask_login import login_required
from models.models import Article

# 创建营养百科蓝图，并设置URL前缀
nutrition_bp = Blueprint('nutrition', __name__, url_prefix='/nutrition')


# ---------------------- 营养百科列表页 ----------------------
@nutrition_bp.route('/', methods=['GET'])
@login_required
def nutrition_index():
    # 查询所有文章，按创建时间倒序排列
    articles = Article.query.order_by(Article.created_at.desc()).all()

    # 渲染列表页面，将文章列表传入模板
    return render_template('nutrition.html', articles=articles)


# ---------------------- 营养百科详情页 ----------------------
@nutrition_bp.route('/<int:article_id>', methods=['GET'])
@login_required
def nutrition_detail(article_id):
    # 根据文章ID查询文章，不存在则返回404
    article = Article.query.get_or_404(article_id)

    # 渲染详情页面，将单篇文章传入模板
    return render_template('nutrition.html', article=article)
