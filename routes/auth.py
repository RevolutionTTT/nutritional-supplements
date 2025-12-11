# routes/auth.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_jwt_extended import create_access_token
from flask_login import login_user, logout_user, login_required
from models.database import db
from models.models import User

auth_bp = Blueprint('auth', __name__)


# ---------------------- 用户注册 ----------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # GET 请求：返回注册页面
    if request.method == 'GET':
        return render_template('register.html')

    # POST 请求：表单提交或 JSON 提交
    data = request.form if request.form else request.get_json()

    # 验证必填字段（用户名、邮箱、密码）
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        # 任意字段为空则报错
        if not data.get(field):
            if request.is_json:
                return jsonify({'error': f'字段 {field} 是必填的'}), 400
            flash(f'字段 {field} 是必填的', 'error')
            return render_template('register.html')

    # 检查用户名是否已存在
    if User.query.filter_by(username=data.get('username')).first():
        if request.is_json:
            return jsonify({'error': '用户名已存在'}), 400
        flash('用户名已存在', 'error')
        return render_template('register.html')

    # 检查邮箱是否已存在
    if User.query.filter_by(email=data.get('email')).first():
        if request.is_json:
            return jsonify({'error': '邮箱已存在'}), 400
        flash('邮箱已存在', 'error')
        return render_template('register.html')

    # 创建新用户
    user = User(
        username=data.get('username'),
        email=data.get('email')
    )
    user.set_password(data.get('password'))  # 设置哈希密码

    # 写入数据库
    db.session.add(user)
    db.session.commit()

    # JSON API 返回
    if request.is_json:
        return jsonify({'message': '用户注册成功'}), 201

    # 浏览器注册返回
    flash('注册成功，请登录', 'success')
    return redirect(url_for('auth.login'))


# ---------------------- 用户登录 ----------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # GET 请求：返回登录页面
    if request.method == 'GET':
        return render_template('login.html')

    # POST：表单或 JSON 登录请求
    data = request.form if request.form else request.get_json()

    # 根据用户名查询用户
    user = User.query.filter_by(username=data.get('username')).first()

    # 验证密码是否正确
    if user and user.check_password(data.get('password')):
        login_user(user)  # 本地 session 登录
        access_token = create_access_token(identity=user.id)  # 为 API 创建 JWT

        # JSON 登录（适用于 SPA、移动端等）
        if request.is_json:
            return jsonify({
                'access_token': access_token,
                'user': user.to_dict(),
                'is_admin': user.is_admin  # 是否管理员
            }), 200

        # 浏览器登录
        if user.is_admin:
            flash('管理员登录成功', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('登录成功', 'success')
            return redirect(url_for('products.get_products'))

    # 登录失败
    if request.is_json:
        return jsonify({'error': '用户名或密码错误'}), 401

    flash('用户名或密码错误', 'error')
    return render_template('login.html')


# ---------------------- 用户退出 ----------------------
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()  # 清除登录状态
    flash('已退出登录', 'success')
    return redirect(url_for('index'))
