from flask import Flask
from models import db, User, Chat, Message, Coupon, Deal, SearchHistory
from datetime import datetime, timezone

def init_db(app: Flask):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qt_shopee.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()
        # Tạo user mặc định nếu chưa có
        default_user = User.query.filter_by(username='default').first()
        if not default_user:
            default_user = User(username='default')
            db.session.add(default_user)
            db.session.commit()
        print(f"✅ Database ready. Default user ID: {default_user.id}")
