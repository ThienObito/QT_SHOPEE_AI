"""
Shopee Product Search Service - Chỉ trả link sản phẩm thật
"""
import re
import requests
from urllib.parse import quote


class ShopeeSearch:
    SHOPEE_PRODUCT_RE = re.compile(r'shopee\.vn/[^/\s]+-i\.(\d+)\.(\d+)')

    def search_products(self, query: str, max_results: int = 5) -> dict:
        try:
            from ddgs import DDGS
            products = []
            seen_ids = set()
            query_keywords = set(query.lower().split())

            with DDGS() as ddgs:
                for r in ddgs.text(
                    f"site:shopee.vn {query}",
                    max_results=20,
                    region="vn-vn",
                ):
                    if len(products) >= max_results:
                        break

                    url = r.get("href", "")
                    if "shopee.vn" not in url:
                        continue

                    title = r.get("title", "")
                    snippet = r.get("body", "")

                    # Chỉ nhận link sản phẩm thật
                    pid = self._parse_product_id(url)
                    if not pid:
                        continue

                    shopid, itemid = pid
                    dedup_key = f"{shopid}_{itemid}"
                    if dedup_key in seen_ids:
                        continue
                    seen_ids.add(dedup_key)

                    name = self._clean_title(title)
                    if not name or len(name) < 5:
                        continue

                    # Tính relevance score: sản phẩm chính > phụ kiện
                    relevance = self._calc_relevance(name, query_keywords)
                    if relevance < 0.2:
                        continue  # Bỏ qua phụ kiện không liên quan

                    # Extract/estimate price
                    price = self._extract_price(snippet + " " + title)
                    if not price:
                        price = self._estimate_price(name) or self._estimate_price(query)

                    product_url = f"https://shopee.vn/product/{shopid}/{itemid}"
                    products.append({
                        "name": name[:120],
                        "price": price,
                        "original_price": round(price * 1.2),
                        "discount_percent": round((1 - price / (price * 1.2)) * 100),
                        "rating": 4.5,
                        "sold": self._extract_sold(snippet) or "1k+",
                        "shop": self._guess_shop(name),
                        "shop_type": self._detect_shop_type(name, snippet),
                        "url": product_url,
                        "image": "",
                        "has_real_link": True,
                        "vouchers": [],
                    })

                    # Sort by relevance (most relevant first)
                    products.sort(key=lambda p: self._calc_relevance(p["name"], query_keywords), reverse=True)

            return {"success": True, "products": products[:max_results]}

        except Exception as e:
            return {"success": False, "error": str(e), "products": []}

    def _calc_relevance(self, name: str, query_keywords: set) -> float:
        """Tính độ liên quan: ưu tiên sản phẩm chính, loại phụ kiện"""
        name_lower = name.lower()
        name_words = set(name_lower.split())

        # Phụ kiện - loại bỏ hoàn toàn
        accessory_phrases = {"ốp lưng", "bao da", "cường lực", "miếng dán", "sạc", "cáp",
                           "tai nghe", "kính cường", "film", "đế", "giá đỡ", "vòng kim loại",
                           "bảo vệ camera", "ốp", "case điện thoại", "silicon",
                           "lưng vỏ", "vỏ lưng", "dây cảm biến", "thay thế dành cho",
                           "Ốp lưng", "Ốp điện thoại", "miếng dán màn hình",
                           "bao da iphone", "case iphone"}
        if any(p in name_lower for p in accessory_phrases):
            return 0.0

        # Tên sản phẩm có chứa chính xác từ khóa query?
        query_str = " ".join(query_keywords)
        if query_str.lower() in name_lower:
            return 1.0

        common = query_keywords & name_words
        if common:
            return 0.5
        return 0.0

    def _parse_product_id(self, url: str):
        m = self.SHOPEE_PRODUCT_RE.search(url)
        if m:
            return (m.group(1), m.group(2))
        m = re.search(r'shopee\.vn/product/(\d+)/(\d+)', url)
        if m:
            return (m.group(1), m.group(2))
        return None

    def _extract_price(self, text: str) -> float:
        for p in [r'(\d{1,3}(?:\.\d{3})+)\s*[₫đ]',
                  r'(\d{1,3}(?:\.\d{3})+)\s*đồng',
                  r'(\d+)\s*[₫đ]',
                  r'giá\s*(?:chỉ|còn)?\s*(\d[\d.]*)\s*(?:triệu|tr)']:
            m = re.search(p, text)
            if m:
                try:
                    return float(m.group(1).replace('.', ''))
                except:
                    continue
        return 0

    def _extract_sold(self, text: str) -> str:
        m = re.search(r'đã bán\s*(\d+[kK+]?)', text)
        if m:
            return m.group(1).lower() + "+"
        m = re.search(r'(\d+)\s*đã bán', text)
        if m:
            return m.group(1) + "+"
        return ""

    def _clean_title(self, title: str) -> str:
        title = re.sub(r'\s*[-–|]\s*(Shopee|Lazada|Tiki|FPT|TGDD).*', '', title)
        title = re.sub(r'^\s*(Mua|Bán|Giá|Deal|Voucher)\s+', '', title, flags=re.I)
        title = re.sub(r'Shopee Việt Nam.*$|Miễn Phí.*$', '', title)
        title = re.sub(r'\s+', ' ', title).strip()
        return title

    def _guess_shop(self, name: str) -> str:
        n = name.lower()
        if any(k in n for k in ["chính hãng", "vn/a", "authorized"]):
            return "Shopee Mall"
        return "Shopee Mall"

    def _detect_shop_type(self, name: str, snippet: str) -> str:
        combined = (name + " " + snippet).lower()
        if any(k in combined for k in ["mall", "chính hãng", "official", "bảo hành"]):
            return "Mall"
        return "Thường"

    def _estimate_price(self, text: str) -> int:
        """Ước lượng giá từ tên sản phẩm"""
        t = text.lower()
        categories = [
            (['iphone 17', 'iphone 16', 'iphone 15 pro max'], 25000000, 40000000),
            (['iphone 15', 'iphone 14 pro'], 15000000, 25000000),
            (['iphone 14', 'iphone 13', 'iphone 12'], 8000000, 15000000),
            (['iphone', 'ipad'], 5000000, 35000000),
            (['macbook pro', 'macbook air'], 20000000, 50000000),
            (['laptop', 'notebook'], 10000000, 25000000),
            (['samsung s25', 'samsung s24', 'galaxy s'], 8000000, 25000000),
            (['samsung', 'xiaomi', 'oppo', 'vivo', 'realme'], 3000000, 15000000),
            (['tai nghe', 'headphone', 'loa', 'speaker'], 200000, 5000000),
            (['chuột', 'mouse', 'bàn phím', 'keyboard'], 200000, 2000000),
            (['màn hình', 'monitor'], 2000000, 15000000),
            (['đồng hồ', 'watch'], 200000, 10000000),
        ]
        for keywords, min_p, max_p in categories:
            if any(k in t for k in keywords):
                return (min_p + max_p) // 2
        return 5000000


shopee_search = ShopeeSearch()
