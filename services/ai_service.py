"""
AI Service - Google Gemini integration for QT_SHOPEE AI
Handles chat, web search, deal finding, and product analysis
"""
import os
import json
import re
from datetime import datetime
from google import genai
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """Bạn là QT_SHOPEE AI - Chuyên gia săn mã giảm giá, voucher và tìm deal hời nhất Việt Nam.

Nhiệm vụ của bạn:
1. Chuyên gia săn deal trên Shopee, Lazada, Tiki, TikTok Shop
2. Chuyên gia mã giảm giá - luôn tìm voucher tối ưu nhất
3. So sánh giá từ nhiều nguồn, tìm giá rẻ nhất
4. Tính giá cuối cùng sau khi áp dụng tất cả voucher

QUY TẮC:
- Luôn trả lời bằng tiếng Việt
- Tối ưu chi phí cho người dùng
- Ưu tiên sản phẩm chính hãng
- Cảnh báo deal ảo, hàng giả
- Đề xuất thời điểm mua tốt nhất (flash sale, ngày đôi)

ĐỊNH DẠNG TRẢ LỜI CHO CHAT THÔNG THƯỜNG:
```
🛍️ **{Tên sản phẩm}**

💰 **Giá gốc:** {giá}₫
🏷️ **Giá khuyến mãi:** {giá}₫
📦 **Nền tảng:** {Shopee/Lazada/Tiki/TikTok}
🎫 **Voucher:** {mã giảm giá} - Giảm {X}%
💎 **Giá cuối cùng:** {giá}₫
🔗 [Mua ngay](link)

💡 Tiết kiệm: {X}% so với giá thị trường
⚡ Flash sale đến: {thời gian}

So sánh giá:
• Shopee: {giá}₫
• Lazada: {giá}₫
• Tiki: {giá}₫
```

KHI NGƯỜI DÙNG HỎI VỀ VOUCHER:
- Tính toán voucher nào lợi nhất dựa trên giá trị đơn hàng
- So sánh % giảm vs giảm tối đa
- Đề xuất mã kèm link

KHI PHÂN TÍCH LINK:
- Trích xuất thông tin sản phẩm từ link
- So sánh giá với các nền tảng khác
- Đề xuất voucher tốt nhất

LUÔN kết thúc bằng câu hỏi gợi ý để người dùng tương tác tiếp."""


class AIService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("❌ GEMINI_API_KEY not found in .env")
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.5-flash"

    def chat(self, message: str, history: list = None) -> str:
        """Gửi tin nhắn và nhận phản hồi từ Gemini"""
        try:
            contents = []
            if history:
                for h in history[-10:]:  # Chỉ lấy 10 tin nhắn gần nhất
                    contents.append({
                        "role": h["role"],
                        "parts": [{"text": h["content"]}]
                    })

            contents.append({
                "role": "user",
                "parts": [{"text": f"{SYSTEM_PROMPT}\n\nNgười dùng: {message}"}]
            })

            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_output_tokens": 2048,
                }
            )

            return response.text

        except Exception as e:
            return f"❌ Lỗi AI: {str(e)}\n\nVui lòng thử lại sau."

    def find_deal(self, query: str) -> str:
        """Tìm deal siêu hời cho sản phẩm"""
        try:
            prompt = f"""{SYSTEM_PROMPT}

NGƯỜI DÙNG YÊU CẦU TÌM DEAL: {query}

Hãy tìm deal tốt nhất hiện tại. Phân tích:
1. Giá thị trường trung bình
2. Giá deal tốt nhất
3. Phần trăm tiết kiệm
4. Voucher có thể áp dụng thêm
5. Thời điểm mua tốt nhất

Trả lời chi tiết dạng bảng so sánh."""

            response = self.client.models.generate_content(
                model=self.model,
                contents=[{"role": "user", "parts": [{"text": prompt}]}],
                config={
                    "temperature": 0.5,
                    "max_output_tokens": 2048,
                }
            )

            return response.text

        except Exception as e:
            return f"❌ Lỗi tìm deal: {str(e)}"

    def analyze_link(self, url: str) -> str:
        """Phân tích link sản phẩm"""
        try:
            platform = self._detect_platform(url)
            prompt = f"""{SYSTEM_PROMPT}

PHÂN TÍCH LINK SẢN PHẨM:
Link: {url}
Nền tảng: {platform}

Hãy phân tích:
1. Loại sản phẩm (từ link)
2. Giá dự kiến
3. So sánh với giá thị trường
4. Voucher có thể áp dụng
5. Đánh giá có nên mua không

Trả lời chi tiết."""

            response = self.client.models.generate_content(
                model=self.model,
                contents=[{"role": "user", "parts": [{"text": prompt}]}],
                config={
                    "temperature": 0.5,
                    "max_output_tokens": 2048,
                }
            )

            return response.text

        except Exception as e:
            return f"❌ Lỗi phân tích link: {str(e)}"

    def optimize_coupon(self, order_value: float, platform: str = "shopee") -> str:
        """Tối ưu voucher cho đơn hàng"""
        try:
            prompt = f"""{SYSTEM_PROMPT}

TỐI ƯU VOUCHER:
Giá trị đơn hàng: {order_value:,.0f}₫
Nền tảng: {platform}

Hãy tính:
1. Voucher % nào lợi nhất
2. Voucher fixed nào lợi nhất
3. Có thể kết hợp voucher không
4. Số tiền tiết kiệm tối đa
5. Giá cuối cùng sau voucher

Đưa ra đề xuất cụ thể với mã voucher."""

            response = self.client.models.generate_content(
                model=self.model,
                contents=[{"role": "user", "parts": [{"text": prompt}]}],
                config={
                    "temperature": 0.5,
                    "max_output_tokens": 1024,
                }
            )

            return response.text

        except Exception as e:
            return f"❌ Lỗi tính voucher: {str(e)}"

    def _detect_platform(self, url: str) -> str:
        """Phát hiện nền tảng từ URL"""
        url_lower = url.lower()
        if "shopee" in url_lower:
            return "Shopee"
        elif "lazada" in url_lower:
            return "Lazada"
        elif "tiki" in url_lower:
            return "Tiki"
        elif "tiktok" in url_lower:
            return "TikTok Shop"
        else:
            return "Khác"


# Singleton instance
ai_service = AIService()
