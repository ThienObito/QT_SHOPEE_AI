"""
Coupon Service - Quản lý mã giảm giá
"""
import re
from datetime import datetime, date
from models import db, Coupon


class CouponService:
    def add_coupon(self, code: str, platform: str, discount_type: str,
                   discount_value: float, min_order: float = 0,
                   max_discount: float = None, expire_date: str = None,
                   description: str = "") -> dict:
        """Thêm mã giảm giá mới"""
        try:
            # Chuẩn hóa
            code = code.strip().upper()
            platform = platform.strip().lower()
            discount_type = discount_type.strip().lower()

            # Kiểm tra trùng
            existing = Coupon.query.filter_by(code=code, platform=platform).first()
            if existing:
                return {"success": False, "error": f"Mã {code} đã tồn tại trên {platform}"}

            expire = None
            if expire_date:
                try:
                    expire = datetime.strptime(expire_date, "%Y-%m-%d").date()
                except ValueError:
                    expire = None

            coupon = Coupon(
                code=code,
                platform=platform,
                discount_type=discount_type,
                discount_value=discount_value,
                min_order=min_order,
                max_discount=max_discount,
                expire_date=expire,
                description=description
            )
            db.session.add(coupon)
            db.session.commit()

            return {
                "success": True,
                "coupon": self._to_dict(coupon)
            }

        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}

    def delete_coupon(self, coupon_id: str) -> dict:
        """Xóa mã giảm giá"""
        try:
            coupon = Coupon.query.get(coupon_id)
            if not coupon:
                return {"success": False, "error": "Mã giảm giá không tồn tại"}
            db.session.delete(coupon)
            db.session.commit()
            return {"success": True, "message": f"Đã xóa mã {coupon.code}"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}

    def update_coupon(self, coupon_id: str, **kwargs) -> dict:
        """Cập nhật mã giảm giá"""
        try:
            coupon = Coupon.query.get(coupon_id)
            if not coupon:
                return {"success": False, "error": "Mã giảm giá không tồn tại"}

            for key, value in kwargs.items():
                if hasattr(coupon, key) and value is not None:
                    if key == 'expire_date' and isinstance(value, str):
                        value = datetime.strptime(value, "%Y-%m-%d").date()
                    setattr(coupon, key, value)

            db.session.commit()
            return {"success": True, "coupon": self._to_dict(coupon)}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}

    def get_all_coupons(self, platform: str = None, active_only: bool = True) -> list:
        """Lấy danh sách mã giảm giá"""
        query = Coupon.query
        if platform:
            query = query.filter_by(platform=platform.lower())
        if active_only:
            query = query.filter_by(is_active=True)
            query = query.filter(
                (Coupon.expire_date.is_(None)) | (Coupon.expire_date >= date.today())
            )
        coupons = query.order_by(Coupon.created_at.desc()).all()
        return [self._to_dict(c) for c in coupons]

    def get_best_coupon(self, platform: str, order_value: float) -> dict:
        """Tìm voucher tốt nhất cho đơn hàng"""
        coupons = Coupon.query.filter_by(
            platform=platform.lower(),
            is_active=True
        ).filter(
            Coupon.min_order <= order_value
        ).filter(
            (Coupon.expire_date.is_(None)) | (Coupon.expire_date >= date.today())
        ).all()

        if not coupons:
            return {"success": False, "error": "Không có voucher phù hợp"}

        best = None
        max_savings = 0

        for c in coupons:
            if c.discount_type == 'percent':
                savings = order_value * (c.discount_value / 100)
                if c.max_discount:
                    savings = min(savings, c.max_discount)
            elif c.discount_type == 'fixed':
                savings = min(c.discount_value, order_value)
            elif c.discount_type == 'shipping':
                savings = c.discount_value
            else:
                continue

            if savings > max_savings:
                max_savings = savings
                best = c

        if best:
            return {
                "success": True,
                "coupon": self._to_dict(best),
                "savings": round(max_savings, 0),
                "final_price": round(order_value - max_savings, 0)
            }
        return {"success": False, "error": "Không có voucher phù hợp"}

    def _to_dict(self, coupon) -> dict:
        return {
            "id": coupon.id,
            "code": coupon.code,
            "platform": coupon.platform,
            "discount_type": coupon.discount_type,
            "discount_value": coupon.discount_value,
            "min_order": coupon.min_order,
            "max_discount": coupon.max_discount,
            "expire_date": coupon.expire_date.isoformat() if coupon.expire_date else None,
            "description": coupon.description,
            "is_active": coupon.is_active
        }

    def parse_coupon_input(self, text: str) -> dict:
        """Parse input tự nhiên thành coupon data"""
        text = text.lower()

        # Detect platform
        platforms = {
            'shopee': ['shopee', 'sp'],
            'lazada': ['lazada', 'lzd'],
            'tiki': ['tiki'],
            'tiktok': ['tiktok', 'tt']
        }
        platform = 'shopee'
        for p, keywords in platforms.items():
            if any(k in text for k in keywords):
                platform = p
                break

        # Extract code
        code_match = re.search(r'mã[:\s]*([A-Za-z0-9_-]{4,})', text)
        code = code_match.group(1).upper() if code_match else "UNKNOWN"

        # Extract discount
        percent_match = re.search(r'giảm\s*(\d+)\s*%', text)
        fixed_match = re.search(r'giảm\s*(\d+[\.\d]*)\s*k', text)

        discount_type = 'percent'
        discount_value = 10

        if percent_match:
            discount_value = float(percent_match.group(1))
        elif fixed_match:
            discount_value = float(fixed_match.group(1).replace('.', '')) * 1000
            discount_type = 'fixed'

        # Extract min_order
        min_match = re.search(r'từ\s*(\d+[\.\d]*)\s*k', text)
        min_order = float(min_match.group(1).replace('.', '')) * 1000 if min_match else 0

        return {
            "code": code,
            "platform": platform,
            "discount_type": discount_type,
            "discount_value": discount_value,
            "min_order": min_order
        }


coupon_service = CouponService()
