from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import uuid

db = SQLAlchemy()


def generate_uuid():
    return str(uuid.uuid4())


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    username = db.Column(db.String(80), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    chats = db.relationship('Chat', backref='user', lazy=True, cascade='all, delete-orphan')


class Chat(db.Model):
    __tablename__ = 'chats'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), default='Chat mới')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    messages = db.relationship('Message', backref='chat', lazy=True,
                               cascade='all, delete-orphan', order_by='Message.created_at')


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    chat_id = db.Column(db.String(36), db.ForeignKey('chats.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Coupon(db.Model):
    __tablename__ = 'coupons'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    code = db.Column(db.String(50), nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # shopee, lazada, tiki, tiktok
    discount_type = db.Column(db.String(20), nullable=False)  # percent, fixed, shipping
    discount_value = db.Column(db.Float, nullable=False)
    min_order = db.Column(db.Float, default=0)
    max_discount = db.Column(db.Float, nullable=True)
    expire_date = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, default='')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Deal(db.Model):
    __tablename__ = 'deals'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    product_name = db.Column(db.String(300), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    original_price = db.Column(db.Float, nullable=False)
    deal_price = db.Column(db.Float, nullable=False)
    discount_percent = db.Column(db.Float, nullable=False)
    voucher_code = db.Column(db.String(50), nullable=True)
    product_url = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.Text, nullable=True)
    is_hot = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    found_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class SearchHistory(db.Model):
    __tablename__ = 'search_history'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    query = db.Column(db.String(300), nullable=False)
    results_summary = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Favorite(db.Model):
    __tablename__ = 'favorites'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    product_name = db.Column(db.String(300), nullable=False)
    product_url = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=True)
    platform = db.Column(db.String(50), nullable=True)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
