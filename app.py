"""
QT_SHOPEE AI - Main Flask Application
"""
import os
import json
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, session, Response
from dotenv import load_dotenv

from database import init_db
from models import db, User, Chat, Message, Coupon, Deal, SearchHistory, Favorite
from services.ai_service import ai_service
from services.coupon_service import coupon_service
from services.search_service import search_service

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()

# Database
init_db(app)


# ───────────────────────────── HELPERS ─────────────────────────────

def get_or_create_user():
    """Get or create default user session"""
    if 'user_id' not in session:
        user = User.query.filter_by(username='default').first()
        if not user:
            user = User(username='default')
            db.session.add(user)
            db.session.commit()
        session['user_id'] = user.id
    return session['user_id']


def get_chat_history(chat_id: str) -> list:
    """Lấy lịch sử chat"""
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at).all()
    return [{"role": m.role, "content": m.content} for m in messages]


def log_search(user_id: str, query: str, result: str = None):
    """Ghi log tìm kiếm"""
    try:
        log = SearchHistory(user_id=user_id, query=query, results_summary=result[:200] if result else None)
        db.session.add(log)
        db.session.commit()
    except:
        db.session.rollback()


# ───────────────────────────── ROUTES ─────────────────────────────

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat với AI"""
    user_id = get_or_create_user()
    data = request.get_json()
    message = data.get('message', '').strip()
    chat_id = data.get('chat_id')

    if not message:
        return jsonify({"success": False, "error": "Vui lòng nhập tin nhắn"})

    # Tạo hoặc lấy chat
    if chat_id:
        chat = Chat.query.get(chat_id)
        if not chat:
            return jsonify({"success": False, "error": "Chat không tồn tại"})
    else:
        # Tạo chat mới với title từ tin nhắn
        title = message[:50] + ('...' if len(message) > 50 else '')
        chat = Chat(user_id=user_id, title=title)
        db.session.add(chat)
        db.session.commit()

    # Lưu tin nhắn user
    user_msg = Message(chat_id=chat.id, role='user', content=message)
    db.session.add(user_msg)
    db.session.commit()

    try:
        # Gọi AI
        history = get_chat_history(chat.id)[-10:-1]  # Không bao gồm tin nhắn vừa gửi
        answer = ai_service.chat(message, history)

        # Lưu tin nhắn AI
        ai_msg = Message(chat_id=chat.id, role='assistant', content=answer)
        db.session.add(ai_msg)
        db.session.commit()

        # Log tìm kiếm
        log_search(user_id, message, answer)

        return jsonify({
            "success": True,
            "chat_id": chat.id,
            "answer": answer
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": f"Lỗi xử lý: {str(e)}"
        })


@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """Chat với AI - Streaming response via SSE"""
    user_id = get_or_create_user()
    data = request.get_json()
    message = data.get('message', '').strip()
    chat_id = data.get('chat_id')

    if not message:
        return jsonify({"success": False, "error": "Vui lòng nhập tin nhắn"})

    # Tạo hoặc lấy chat
    if chat_id:
        chat = Chat.query.get(chat_id)
        if not chat:
            return jsonify({"success": False, "error": "Chat không tồn tại"})
    else:
        title = message[:50] + ('...' if len(message) > 50 else '')
        chat = Chat(user_id=user_id, title=title)
        db.session.add(chat)
        db.session.commit()

    # Lưu tin nhắn user
    user_msg = Message(chat_id=chat.id, role='user', content=message)
    db.session.add(user_msg)
    db.session.commit()

    def generate():
        full_response = ""
        try:
            history = get_chat_history(chat.id)[-10:-1]
            for chunk in ai_service.chat_stream(message, history):
                full_response += chunk
                yield f"data: {json.dumps({'chat_id': chat.id, 'chunk': chunk})}\n\n"

            # Lưu tin nhắn AI
            with app.app_context():
                ai_msg = Message(chat_id=chat.id, role='assistant', content=full_response)
                db.session.add(ai_msg)
                db.session.commit()
                log_search(user_id, message, full_response)

            yield f"data: {json.dumps({'done': True, 'chat_id': chat.id})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )


@app.route('/api/find-deal', methods=['POST'])
def find_deal():
    """Tìm deal siêu hời"""
    data = request.get_json()
    query = data.get('query', '').strip()

    if not query:
        return jsonify({"success": False, "error": "Vui lòng nhập sản phẩm cần tìm deal"})

    try:
        result = ai_service.find_deal(query)
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/analyze-link', methods=['POST'])
def analyze_link():
    """Phân tích link sản phẩm"""
    data = request.get_json()
    url = data.get('url', '').strip()

    if not url:
        return jsonify({"success": False, "error": "Vui lòng dán link sản phẩm"})

    try:
        result = ai_service.analyze_link(url)
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/coupon/add', methods=['POST'])
def add_coupon():
    """Thêm mã giảm giá"""
    data = request.get_json()
    text = data.get('text', '')

    if text:
        # Tự động parse từ text
        parsed = coupon_service.parse_coupon_input(text)
        result = coupon_service.add_coupon(**parsed)
    else:
        result = coupon_service.add_coupon(
            code=data.get('code', '').strip().upper(),
            platform=data.get('platform', 'shopee').lower(),
            discount_type=data.get('discount_type', 'percent'),
            discount_value=float(data.get('discount_value', 0)),
            min_order=float(data.get('min_order', 0)),
            max_discount=float(data['max_discount']) if data.get('max_discount') else None,
            expire_date=data.get('expire_date'),
            description=data.get('description', '')
        )

    return jsonify(result)


@app.route('/api/coupon/list', methods=['GET'])
def list_coupons():
    """Danh sách mã giảm giá"""
    platform = request.args.get('platform')
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    coupons = coupon_service.get_all_coupons(platform, active_only)
    return jsonify({"success": True, "coupons": coupons})


@app.route('/api/coupon/delete/<coupon_id>', methods=['DELETE'])
def delete_coupon(coupon_id):
    """Xóa mã giảm giá"""
    result = coupon_service.delete_coupon(coupon_id)
    return jsonify(result)


@app.route('/api/coupon/optimize', methods=['POST'])
def optimize_coupon():
    """Tối ưu voucher cho đơn hàng"""
    data = request.get_json()
    order_value = float(data.get('order_value', 0))
    platform = data.get('platform', 'shopee')

    if order_value <= 0:
        return jsonify({"success": False, "error": "Vui lòng nhập giá trị đơn hàng"})

    # Tìm trong DB trước
    best = coupon_service.get_best_coupon(platform, order_value)
    if best['success']:
        best['ai_analysis'] = ai_service.optimize_coupon(order_value, platform)
        return jsonify(best)

    # Fallback: hỏi AI
    ai_result = ai_service.optimize_coupon(order_value, platform)
    return jsonify({"success": True, "source": "ai", "analysis": ai_result})


@app.route('/api/search', methods=['POST'])
def search():
    """Tìm kiếm thông minh với fuzzy"""
    data = request.get_json()
    query = data.get('query', '').strip()

    if not query:
        return jsonify({"success": False, "error": "Vui lòng nhập từ khóa"})

    # Fuzzy search
    fuzzy_results = search_service.fuzzy_match(query)
    # Normalize
    normalized = search_service.normalize_query(query)
    # Price range
    price_range = search_service.extract_price_range(query)

    return jsonify({
        "success": True,
        "original": query,
        "normalized": normalized,
        "suggestions": fuzzy_results,
        "price_range": price_range
    })


@app.route('/api/chats', methods=['GET'])
def list_chats():
    """Danh sách chat"""
    user_id = get_or_create_user()
    chats = Chat.query.filter_by(user_id=user_id).order_by(Chat.updated_at.desc()).all()
    return jsonify({
        "success": True,
        "chats": [{
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat(),
            "message_count": len(c.messages)
        } for c in chats]
    })


@app.route('/api/chats/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Lấy chi tiết chat"""
    chat = Chat.query.get(chat_id)
    if not chat:
        return jsonify({"success": False, "error": "Chat không tồn tại"})

    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at).all()
    return jsonify({
        "success": True,
        "chat": {
            "id": chat.id,
            "title": chat.title
        },
        "messages": [{
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat()
        } for m in messages]
    })


@app.route('/api/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Xóa chat"""
    chat = Chat.query.get(chat_id)
    if not chat:
        return jsonify({"success": False, "error": "Chat không tồn tại"})

    db.session.delete(chat)
    db.session.commit()
    return jsonify({"success": True})


@app.route('/api/chats/<chat_id>/title', methods=['PUT'])
def update_chat_title(chat_id):
    """Cập nhật tiêu đề chat"""
    chat = Chat.query.get(chat_id)
    if not chat:
        return jsonify({"success": False, "error": "Chat không tồn tại"})

    data = request.get_json()
    chat.title = data.get('title', chat.title)
    db.session.commit()
    return jsonify({"success": True})


@app.route('/api/history', methods=['GET'])
def search_history():
    """Lịch sử tìm kiếm"""
    user_id = get_or_create_user()
    history = SearchHistory.query.filter_by(user_id=user_id).order_by(
        SearchHistory.created_at.desc()).limit(20).all()
    return jsonify({
        "success": True,
        "history": [{
            "id": h.id,
            "query": h.query,
            "created_at": h.created_at.isoformat()
        } for h in history]
    })


@app.route('/api/coupon/parse', methods=['POST'])
def parse_coupon_text():
    """Parse text thành coupon data"""
    data = request.get_json()
    text = data.get('text', '')
    if not text:
        return jsonify({"success": False, "error": "Vui lòng nhập nội dung"})

    parsed = coupon_service.parse_coupon_input(text)
    return jsonify({"success": True, "parsed": parsed})


@app.route('/api/favorites', methods=['GET'])
def list_favorites():
    user_id = get_or_create_user()
    favs = Favorite.query.filter_by(user_id=user_id).order_by(Favorite.created_at.desc()).all()
    return jsonify({"success": True, "favorites": [{
        "id": f.id,
        "product_name": f.product_name,
        "product_url": f.product_url,
        "image_url": f.image_url,
        "price": f.price,
        "platform": f.platform,
        "note": f.note,
        "created_at": f.created_at.isoformat()
    } for f in favs]})


@app.route('/api/favorites/add', methods=['POST'])
def add_favorite():
    user_id = get_or_create_user()
    data = request.get_json()
    fav = Favorite(
        user_id=user_id,
        product_name=data.get('product_name', 'Unknown'),
        product_url=data.get('product_url'),
        image_url=data.get('image_url'),
        price=data.get('price'),
        platform=data.get('platform'),
        note=data.get('note')
    )
    db.session.add(fav)
    db.session.commit()
    return jsonify({"success": True, "id": fav.id})


@app.route('/api/favorites/<fav_id>', methods=['DELETE'])
def delete_favorite(fav_id):
    fav = Favorite.query.get(fav_id)
    if not fav:
        return jsonify({"success": False, "error": "Not found"})
    db.session.delete(fav)
    db.session.commit()
    return jsonify({"success": True})


# ───────────────────────────── MAIN ─────────────────────────────

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    print(f"🚀 QT_SHOPEE AI running on http://0.0.0.0:{port}")
    print(f"📡 Gemini AI model: gemini-2.5-flash")
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
