"""
Search Service - Fuzzy search for product names
"""
import re
from difflib import SequenceMatcher


class SearchService:
    # Từ điển tên sản phẩm thông dụng và biến thể
    COMMON_MISTAKES = {
        'iphone': ['iphone', 'iphoe', 'ifon', 'ipon', 'ai phôn', 'ai phong', 'ip'],
        'samsung': ['samsung', 'sansung', 'sam sung', 'xam sung', 'ss'],
        'xiaomi': ['xiaomi', 'xiaome', 'xao mi', 'xiao mi', 'xịaomi'],
        'oppo': ['oppo', 'opo', 'op po'],
        'vivo': ['vivo', 'vi vo', 'vivoo'],
        'realme': ['realme', 'real me', 'riem'],
        'nokia': ['nokia', 'nokial', 'noc kia'],
        'sony': ['sony', 'xony', 'so ny'],
        'lg': ['lg', 'el gi', 'elji'],
        'dell': ['dell', 'del', 'den', 'đen'],
        'hp': ['hp', 'h p', 'hach pi'],
        'lenovo': ['lenovo', 'le novo', 'len ovo'],
        'acer': ['acer', 'ace', 'ase'],
        'asus': ['asus', 'a sus', 'a xux'],
        'macbook': ['macbook', 'mac book', 'mác búc', 'macbok', 'mackbook'],
        'laptop': ['laptop', 'lap top', 'láp tóp', 'máy tính xách tay', 'notebook'],
        'tai nghe': ['tai nghe', 'tainghe', 'tai ngót', 'headphone', 'earphone'],
        'chuột': ['chuột', 'chuot', 'mouse'],
        'bàn phím': ['bàn phím', 'ban phim', 'keyboard', 'bàn phím cơ'],
        'màn hình': ['màn hình', 'man hinh', 'monitor', 'screen'],
    }

    def fuzzy_match(self, query: str, threshold: float = 0.6) -> list:
        """Tìm kiếm mờ - match tên sản phẩm với từ khóa"""
        query = query.lower().strip()
        matches = []

        for canonical, variants in self.COMMON_MISTAKES.items():
            # Check exact variant match
            for variant in variants:
                if variant in query or query in variant:
                    matches.append((canonical, 1.0))
                    break
            else:
                # Check similarity
                for variant in variants:
                    ratio = SequenceMatcher(None, query, variant).ratio()
                    if ratio >= threshold:
                        matches.append((canonical, ratio))

            # Check word-level match
            query_words = set(re.sub(r'[^a-z0-9\s]', ' ', query).split())
            variant_words = set()
            for v in variants:
                variant_words.update(re.sub(r'[^a-z0-9\s]', ' ', v).split())

            common = query_words & variant_words
            if common:
                score = len(common) / max(len(query_words), len(variant_words))
                if score >= threshold:
                    matches.append((canonical, max(score, 0.7)))

        # Deduplicate and sort
        seen = set()
        unique_matches = []
        for name, score in sorted(matches, key=lambda x: -x[1]):
            if name not in seen:
                seen.add(name)
                unique_matches.append({"name": name, "score": round(score, 2)})

        return unique_matches[:5]

    def normalize_query(self, query: str) -> str:
        """Chuẩn hóa từ khóa tìm kiếm"""
        query = query.lower().strip()
        # Remove special characters
        query = re.sub(r'[^\w\s]', ' ', query)
        # Remove extra spaces
        query = re.sub(r'\s+', ' ', query)
        # Try to match common mistakes
        matches = self.fuzzy_match(query)
        if matches and matches[0]['score'] >= 0.7:
            # Replace with canonical name
            for old, new in [
                ('macbook', 'MacBook'),
                ('tai nghe', 'tai nghe'),
                ('laptop', 'laptop'),
            ]:
                if matches[0]['name'] == old:
                    query = query.replace(matches[0]['name'], new)
        return query.strip()

    def extract_price_range(self, query: str) -> dict:
        """Trích xuất khoảng giá từ câu hỏi"""
        price_info = {"min": 0, "max": float('inf')}

        # Patterns: dưới X triệu, trên X triệu, từ X đến Y, khoảng X
        patterns = [
            (r'dưới\s*(\d+[\.\d]*)\s*(triệu|tr|k)\b', 'max'),
            (r'trên\s*(\d+[\.\d]*)\s*(triệu|tr|k)\b', 'min'),
            (r'từ\s*(\d+[\.\d]*)\s*(triệu|tr|k)?\s*(đến|-\s*)\s*(\d+[\.\d]*)\s*(triệu|tr|k)?', 'range'),
            (r'giá\s*(\d+[\.\d]*)\s*(triệu|tr|k)\b', 'exact'),
            (r'(\d+[\.\d]*)\s*(triệu|tr)\b', 'max'),
        ]

        for pattern, ptype in patterns:
            match = re.search(pattern, query.lower())
            if match:
                if ptype == 'range':
                    val1 = self._parse_price(match.group(1), match.group(2))
                    val2 = self._parse_price(match.group(4), match.group(5))
                    price_info["min"] = val1
                    price_info["max"] = val2
                elif ptype == 'max':
                    val = self._parse_price(match.group(1), match.group(2))
                    price_info["max"] = val
                elif ptype == 'min':
                    val = self._parse_price(match.group(1), match.group(2))
                    price_info["min"] = val
                elif ptype == 'exact':
                    val = self._parse_price(match.group(1), match.group(2))
                    price_info["max"] = val * 1.1
                    price_info["min"] = val * 0.9

        return price_info

    def _parse_price(self, value: str, unit: str) -> float:
        """Parse giá trị tiền tệ"""
        value = float(value.replace('.', ''))
        if unit in ('triệu', 'tr'):
            return value * 1_000_000
        elif unit == 'k':
            return value * 1_000
        return value


search_service = SearchService()
