from flask import Blueprint, render_template
from models.models import Announcement

# 创建公告蓝图，用于管理公告相关路由
announcement_bp = Blueprint('announcement', __name__)

@announcement_bp.route('/announcement')
def show_announcement():
    # 获取最新一条公告（按创建时间倒序排列）
    announcement = Announcement.query.order_by(Announcement.created_at.desc()).first()

    # 将公告对象传递给模板进行展示
    return render_template('announcement.html', announcement=announcement)

