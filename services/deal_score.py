"""
Deal Score Calculator + Product Filter for QTDEAL.AI
"""
import re

# Deal Score weights
W_DISCOUNT = 0.40   # Mức giảm giá
W_SHOP_TRUST = 0.30  # Uy tín shop
W_RATING = 0.20      # Đánh giá người mua
W_SALES = 0.10       # Số lượng bán

SHOP_TYPE_SCORE = {
    "mall": 1.0,
    "yêu thích": 0.9,
    "yeu thich": 0.9,
    "favourite": 0.9,
    "thường": 0.5,
    "thuong": 0.5,
    "normal": 0.5,
    "": 0.5,
}


def calc_deal_score(product: dict) -> dict:
    """Calculate Deal Score for a product (0-100)"""
    # Input validation
    if not product.get("name"):
        return {**product, "deal_score": 0, "filtered": True, "filter_reason": "No name"}

    # 1. Discount score (0-100)
    discount = float(product.get("discount_percent", 0) or 0)
    discount_score = min(discount * 3, 100)  # 33% discount = 100 points

    # 2. Shop trust score (0-100)
    shop_type = (product.get("shop_type", "") or "").lower().strip()
    trust_score = SHOP_TYPE_SCORE.get(shop_type, 0.5) * 100

    # 3. Rating score (0-100)
    rating = float(product.get("rating", 0) or 0)
    rating_score = (rating / 5.0) * 100

    # 4. Sales score (0-100)
    sold_str = str(product.get("sold", "0") or "0")
    sold_num = _parse_sold(sold_str)
    sales_score = min(sold_num / 100, 100)  # 100+ sold = 100 points

    # Calculate weighted score
    deal_score = (
        W_DISCOUNT * discount_score +
        W_SHOP_TRUST * trust_score +
        W_RATING * rating_score +
        W_SALES * sales_score
    )

    # Filter checks
    filtered = False
    filter_reason = None

    # Check: thiếu thông tin
    if not product.get("price") or float(product.get("price", 0)) <= 0:
        filtered = True
        filter_reason = "Missing price"

    # Check: giá bất thường (> 500tr)
    if not filtered and float(product.get("price", 0)) > 500_000_000:
        filtered = True
        filter_reason = "Abnormal price"

    # Check: rating quá thấp
    if not filtered and rating < 3.0 and rating > 0:
        filtered = True
        filter_reason = "Low rating"

    # Check: không có đánh giá
    if not filtered and rating == 0 and sold_num == 0:
        filtered = True
        filter_reason = "No reviews"

    return {
        **product,
        "deal_score": round(deal_score, 1),
        "discount_score": round(discount_score, 1),
        "trust_score": round(trust_score, 1),
        "rating_score": round(rating_score, 1),
        "sales_score": round(sales_score, 1),
        "filtered": filtered,
        "filter_reason": filter_reason,
        "final_price": _calc_final_price(product),
    }


def rank_products(products: list, min_score: float = 30) -> list:
    """Calculate scores, filter, sort, return top 10"""
    results = []

    for p in products:
        scored = calc_deal_score(p)
        results.append(scored)

    # Sort by deal_score descending
    results.sort(key=lambda x: (-x.get("filtered", False), -x.get("deal_score", 0)))

    # Take top items (include filtered too but mark them)
    top = results[:10]

    return top


def _calc_final_price(product: dict) -> float:
    """Calculate final price after vouchers"""
    price = float(product.get("price", 0) or 0)
    vouchers = product.get("vouchers", [])

    if not vouchers:
        return price

    total_discount = 0
    for v in vouchers:
        v = str(v).lower()
        # Match patterns like "giảm 50k", "giảm 10%", "freeship"
        m = re.search(r'giảm\s*(\d+)\s*k', v)
        if m:
            total_discount += float(m.group(1)) * 1000
        m = re.search(r'giảm\s*(\d+)\s*%', v)
        if m:
            pct = float(m.group(1))
            total_discount = max(total_discount, price * pct / 100)

    return max(price - total_discount, 0)


def _parse_sold(sold_str: str) -> int:
    """Parse sold string like '5.2k', '1.2tr', '1.000' into number"""
    if not sold_str:
        return 0
    sold_str = str(sold_str).strip().lower().replace(" ", "")

    m = re.match(r'([\d.]+)\s*(k|tr|nghìn|triệu)?', sold_str)
    if not m:
        try:
            return int(float(sold_str.replace(".", "").replace(",", ".")))
        except:
            return 0

    val = float(m.group(1).replace(".", "").replace(",", "."))
    unit = m.group(2) or ""

    if unit in ("k", "nghìn"):
        return int(val * 1000)
    elif unit in ("tr", "triệu"):
        return int(val * 1_000_000)
    else:
        return int(val)
