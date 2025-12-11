# utils/notifications.py
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from threading import Thread
from flask import current_app
from models.models import Product


def check_low_stock():
    """检查低库存商品"""
    low_stock_products = Product.query.filter(
        Product.stock_quantity <= 10,
        Product.is_active == True
    ).all()

    if low_stock_products:
        # 发送邮件通知管理员
        message = "以下商品库存不足：\n\n"
        for product in low_stock_products:
            message += f"{product.name} - 当前库存: {product.stock_quantity}\n"

        send_email_async(
            to=current_app.config['ADMIN_EMAIL'],
            subject='库存预警通知',
            content=message
        )


def send_order_confirmation(order,user):
    """发送订单确认邮件"""
    subject = f"订单确认 - #{order.id}"
    content = f"""
    尊敬的{user.full_name}：

    感谢您的购买！您的订单已成功创建。

    订单号：{order.id}
    订单金额：¥{order.total_amount}
    订单状态：{order.status}

    订单详情：
    {generate_order_details(order)}

    我们将尽快处理您的订单。

    谢谢！
    营养补充剂销售系统
    """

    send_email_async(user.email,subject,content)


def send_email_async(to,subject,content):
    """异步发送邮件"""

    def send_email():
        try:
            # 配置邮件服务器（这里使用SMTP示例）
            msg = MIMEText(content,'plain','utf-8')
            msg['From'] = current_app.config['MAIL_USERNAME']
            msg['To'] = to
            msg['Subject'] = Header(subject,'utf-8')

            server = smtplib.SMTP(current_app.config['MAIL_SERVER'],current_app.config['MAIL_PORT'])
            server.starttls()
            server.login(current_app.config['MAIL_USERNAME'],current_app.config['MAIL_PASSWORD'])
            server.send_message(msg)
            server.quit()
        except Exception as e:
            current_app.logger.error(f'发送邮件失败: {str(e)}')

    thread = Thread(target=send_email)
    thread.start()


def generate_order_details(order):
    """生成订单详情文本"""
    details = ""
    for item in order.order_items:
        details += f"{item.product.name} x {item.quantity} = ¥{item.unit_price * item.quantity}\n"
    return details