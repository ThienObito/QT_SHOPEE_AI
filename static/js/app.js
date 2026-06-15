/* ─── QT_SHOPEE AI ─── Frontend Application ─── */

const App = {
  state: {
    currentChatId: null,
    isStreaming: false,
    chats: [],
    coupons: [],
    theme: localStorage.getItem('theme') || 'light',
    sidebarOpen: false,
  },

  init() {
    this.loadTheme();
    this.loadChats();
    this.setupEventListeners();
    this.setupAutoResize();

    if (this.state.theme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  },

  /* ─── THEME ─── */
  loadTheme() {
    const saved = localStorage.getItem('theme');
    if (saved === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
      this.state.theme = 'dark';
    }
  },

  toggleTheme() {
    const isDark = this.state.theme === 'dark';
    this.state.theme = isDark ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', this.state.theme);
    localStorage.setItem('theme', this.state.theme);
    document.getElementById('theme-icon').textContent = isDark ? '☀️' : '🌙';
  },

  /* ─── EVENT LISTENERS ─── */
  setupEventListeners() {
    // Send message
    document.getElementById('send-btn').addEventListener('click', () => this.sendMessage());
    document.getElementById('message-input').addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // New chat
    document.getElementById('new-chat-btn').addEventListener('click', () => this.newChat());

    // Theme toggle
    document.getElementById('theme-toggle').addEventListener('click', () => this.toggleTheme());

    // Sidebar nav
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', () => {
        const action = item.dataset.action;
        if (action === 'new-chat') this.newChat();
        else if (action === 'vouchers') this.showCoupons();
        else if (action === 'deals') this.showDealFinder();
        else if (action === 'settings') this.showSettings();

        // Highlight active
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        item.classList.add('active');
      });
    });

    // Hamburger menu (mobile)
    document.getElementById('hamburger').addEventListener('click', () => {
      this.state.sidebarOpen = !this.state.sidebarOpen;
      document.querySelector('.sidebar').classList.toggle('open');
    });

    // Click outside to close sidebar (mobile)
    document.getElementById('main-content').addEventListener('click', () => {
      if (window.innerWidth <= 768 && this.state.sidebarOpen) {
        this.state.sidebarOpen = false;
        document.querySelector('.sidebar').classList.remove('open');
      }
    });

    // Suggestion chips
    document.querySelectorAll('.suggestion-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const text = chip.textContent.trim();
        document.getElementById('message-input').value = text;
        this.sendMessage();
      });
    });
  },

  setupAutoResize() {
    const input = document.getElementById('message-input');
    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    });
  },

  /* ─── CHAT ─── */
  async sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    if (!message || this.state.isStreaming) return;

    input.value = '';
    input.style.height = 'auto';
    this.state.isStreaming = true;
    document.getElementById('send-btn').disabled = true;

    // Hide welcome
    document.getElementById('welcome-screen').classList.add('hidden');
    document.getElementById('messages-area').classList.remove('hidden');

    // Add user message
    this.addMessage('user', message);

    // Show typing
    this.showTyping();

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          chat_id: this.state.currentChatId
        })
      });

      const data = await response.json();
      this.hideTyping();

      if (data.success) {
        this.state.currentChatId = data.chat_id;
        this.addMessage('assistant', data.answer);
        this.loadChats(); // Refresh sidebar
      } else {
        this.showToast(data.error || 'Lỗi xử lý tin nhắn', 'error');
      }

    } catch (err) {
      this.hideTyping();
      this.showToast('Lỗi kết nối đến server', 'error');
    }

    this.state.isStreaming = false;
    document.getElementById('send-btn').disabled = false;
    input.focus();
  },

  addMessage(role, content) {
    const container = document.getElementById('messages-container');
    const div = document.createElement('div');
    div.className = `message ${role}`;

    const avatar = role === 'user' ? '👤' : '🤖';
    // Convert markdown-style formatting to HTML
    let html = content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');

    div.innerHTML = `
      <div class="message-avatar">${avatar}</div>
      <div class="message-content">${html}</div>
    `;

    container.appendChild(div);
    this.scrollToBottom();
  },

  showTyping() {
    const container = document.getElementById('messages-container');
    const div = document.createElement('div');
    div.className = 'typing-indicator';
    div.id = 'typing-indicator';
    div.innerHTML = `
      <div class="message-avatar">🤖</div>
      <div class="typing-dots">
        <span></span><span></span><span></span>
      </div>
    `;
    container.appendChild(div);
    this.scrollToBottom();
  },

  hideTyping() {
    const typing = document.getElementById('typing-indicator');
    if (typing) typing.remove();
  },

  scrollToBottom() {
    const container = document.getElementById('chat-container');
    setTimeout(() => {
      container.scrollTop = container.scrollHeight;
    }, 50);
  },

  newChat() {
    this.state.currentChatId = null;
    document.getElementById('welcome-screen').classList.remove('hidden');
    document.getElementById('messages-area').classList.add('hidden');
    document.getElementById('messages-container').innerHTML = '';
    document.getElementById('message-input').value = '';
    document.getElementById('message-input').focus();

    // Deselect all chat items
    document.querySelectorAll('.chat-item').forEach(item => item.classList.remove('active'));
  },

  /* ─── CHAT LIST ─── */
  async loadChats() {
    try {
      const response = await fetch('/api/chats');
      const data = await response.json();
      if (data.success) {
        this.state.chats = data.chats;
        this.renderChatList();
      }
    } catch (err) {
      console.error('Failed to load chats:', err);
    }
  },

  renderChatList() {
    const list = document.getElementById('chat-list');
    list.innerHTML = '';

    if (this.state.chats.length === 0) {
      list.innerHTML = '<div style="padding: 20px; text-align: center; opacity: 0.5; font-size: 13px;">Chưa có cuộc trò chuyện nào</div>';
      return;
    }

    this.state.chats.forEach(chat => {
      const div = document.createElement('div');
      div.className = `chat-item ${chat.id === this.state.currentChatId ? 'active' : ''}`;
      div.innerHTML = `
        <span class="chat-title">${this.escapeHtml(chat.title)}</span>
        <button class="chat-delete" data-id="${chat.id}">✕</button>
      `;

      div.querySelector('.chat-title').addEventListener('click', () => this.loadChat(chat.id));
      div.querySelector('.chat-delete').addEventListener('click', (e) => {
        e.stopPropagation();
        this.deleteChat(chat.id);
      });

      list.appendChild(div);
    });
  },

  async loadChat(chatId) {
    try {
      const response = await fetch(`/api/chats/${chatId}`);
      const data = await response.json();

      if (data.success) {
        this.state.currentChatId = chatId;
        document.getElementById('welcome-screen').classList.add('hidden');
        document.getElementById('messages-area').classList.remove('hidden');

        const container = document.getElementById('messages-container');
        container.innerHTML = '';

        data.messages.forEach(msg => {
          this.addMessage(msg.role, msg.content);
        });

        this.renderChatList();
        this.scrollToBottom();

        // Close sidebar on mobile
        if (window.innerWidth <= 768) {
          this.state.sidebarOpen = false;
          document.querySelector('.sidebar').classList.remove('open');
        }
      }
    } catch (err) {
      this.showToast('Lỗi tải chat', 'error');
    }
  },

  async deleteChat(chatId) {
    if (!confirm('Xóa cuộc trò chuyện này?')) return;

    try {
      const response = await fetch(`/api/chats/${chatId}`, { method: 'DELETE' });
      const data = await response.json();

      if (data.success) {
        if (this.state.currentChatId === chatId) {
          this.newChat();
        }
        this.loadChats();
        this.showToast('Đã xóa chat', 'success');
      }
    } catch (err) {
      this.showToast('Lỗi xóa chat', 'error');
    }
  },

  /* ─── COUPONS ─── */
  async loadCoupons() {
    try {
      const response = await fetch('/api/coupon/list');
      const data = await response.json();
      if (data.success) {
        this.state.coupons = data.coupons;
        this.renderCoupons();
      }
    } catch (err) {
      console.error('Failed to load coupons:', err);
    }
  },

  renderCoupons() {
    const list = document.getElementById('coupon-list');
    if (!list) return;

    if (this.state.coupons.length === 0) {
      list.innerHTML = '<div style="text-align:center; padding: 20px; color: var(--text-muted);">Chưa có mã giảm giá nào</div>';
      return;
    }

    list.innerHTML = this.state.coupons.map(c => `
      <div class="coupon-card">
        <div>
          <div class="coupon-code">${this.escapeHtml(c.code)}</div>
          <div class="coupon-info">${this.escapeHtml(c.platform)}</div>
        </div>
        <div class="coupon-value">
          ${c.discount_type === 'percent' ? c.discount_value + '%' : c.discount_value.toLocaleString() + '₫'}
          ${c.min_order > 0 ? `<br><span class="coupon-expired">Đơn từ ${c.min_order.toLocaleString()}₫</span>` : ''}
        </div>
      </div>
    `).join('');
  },

  showCoupons() {
    this.loadCoupons();
    document.getElementById('modal-overlay').classList.add('open');
    document.getElementById('modal-title').textContent = '🎫 Mã giảm giá';
    document.getElementById('modal-body').innerHTML = `
      <div style="margin-bottom: 16px;">
        <button class="btn btn-primary" onclick="App.showAddCoupon()">+ Thêm mã</button>
        <button class="btn btn-secondary" onclick="App.optimizeCoupon()">💰 Tối ưu</button>
      </div>
      <div id="coupon-list"></div>
    `;
    this.renderCoupons();
  },

  showAddCoupon() {
    document.getElementById('modal-body').innerHTML = `
      <div class="form-group">
        <label>Mã giảm giá</label>
        <input type="text" id="coupon-code" placeholder="VD: SHOPEE30K" class="input">
      </div>
      <div class="form-group">
        <label>Nền tảng</label>
        <select id="coupon-platform">
          <option value="shopee">Shopee</option>
          <option value="lazada">Lazada</option>
          <option value="tiki">Tiki</option>
          <option value="tiktok">TikTok Shop</option>
        </select>
      </div>
      <div class="form-group">
        <label>Loại giảm giá</label>
        <select id="coupon-type">
          <option value="percent">% giảm</option>
          <option value="fixed">Giảm tiền mặt</option>
          <option value="shipping">Giảm phí ship</option>
        </select>
      </div>
      <div class="form-group">
        <label>Giá trị giảm</label>
        <input type="number" id="coupon-value" placeholder="VD: 10 (nếu %) hoặc 30000 (nếu tiền)" step="1000">
      </div>
      <div class="form-group">
        <label>Đơn tối thiểu (₫) - không bắt buộc</label>
        <input type="number" id="coupon-min" placeholder="VD: 500000" step="1000">
      </div>
      <div class="form-group">
        <label>Giảm tối đa (₫) - không bắt buộc</label>
        <input type="number" id="coupon-max" placeholder="VD: 50000">
      </div>
      <div class="form-group">
        <label>Ngày hết hạn (không bắt buộc)</label>
        <input type="date" id="coupon-expire">
      </div>
      <div class="form-actions">
        <button class="btn btn-secondary" onclick="App.showCoupons()">← Quay lại</button>
        <button class="btn btn-primary" onclick="App.saveCoupon()">💾 Lưu</button>
      </div>
    `;
  },

  async saveCoupon() {
    const data = {
      code: document.getElementById('coupon-code').value.trim(),
      platform: document.getElementById('coupon-platform').value,
      discount_type: document.getElementById('coupon-type').value,
      discount_value: parseFloat(document.getElementById('coupon-value').value) || 0,
      min_order: parseFloat(document.getElementById('coupon-min').value) || 0,
      max_discount: document.getElementById('coupon-max').value || null,
      expire_date: document.getElementById('coupon-expire').value || null,
    };

    if (!data.code || data.discount_value <= 0) {
      this.showToast('Vui lòng nhập mã và giá trị giảm giá', 'error');
      return;
    }

    try {
      const response = await fetch('/api/coupon/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      const result = await response.json();

      if (result.success) {
        this.showToast('✅ Đã thêm mã giảm giá', 'success');
        this.showCoupons();
      } else {
        this.showToast(result.error || 'Lỗi thêm mã', 'error');
      }
    } catch (err) {
      this.showToast('Lỗi kết nối', 'error');
    }
  },

  async optimizeCoupon() {
    document.getElementById('modal-body').innerHTML = `
      <div class="form-group">
        <label>Giá trị đơn hàng (₫)</label>
        <input type="number" id="order-value" placeholder="VD: 800000" step="1000">
      </div>
      <div class="form-group">
        <label>Nền tảng</label>
        <select id="order-platform">
          <option value="shopee">Shopee</option>
          <option value="lazada">Lazada</option>
          <option value="tiki">Tiki</option>
          <option value="tiktok">TikTok Shop</option>
        </select>
      </div>
      <div class="form-actions">
        <button class="btn btn-secondary" onclick="App.showCoupons()">← Quay lại</button>
        <button class="btn btn-primary" onclick="App.checkOptimize()">🔍 Tìm voucher tốt nhất</button>
      </div>
      <div id="optimize-result" class="mt-16"></div>
    `;
  },

  async checkOptimize() {
    const orderValue = parseFloat(document.getElementById('order-value').value);
    const platform = document.getElementById('order-platform').value;

    if (!orderValue || orderValue <= 0) {
      this.showToast('Vui lòng nhập giá trị đơn hàng', 'error');
      return;
    }

    const resultDiv = document.getElementById('optimize-result');
    resultDiv.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';

    try {
      const response = await fetch('/api/coupon/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ order_value: orderValue, platform })
      });
      const data = await response.json();

      if (data.success) {
        if (data.coupon) {
          resultDiv.innerHTML = `
            <div style="background: var(--bg-secondary); padding: 16px; border-radius: var(--radius); border: 1px solid var(--border);">
              <div style="font-size: 18px; font-weight: 700; color: var(--primary); margin-bottom: 8px;">
                💰 Tiết kiệm: ${data.savings.toLocaleString()}₫
              </div>
              <div><strong>Mã:</strong> <span class="coupon-code">${data.coupon.code}</span></div>
              <div><strong>Giảm:</strong> ${data.coupon.discount_type === 'percent' ? data.coupon.discount_value + '%' : data.coupon.discount_value.toLocaleString() + '₫'}</div>
              <div><strong>Giá cuối:</strong> ${data.final_price.toLocaleString()}₫</div>
              <div style="margin-top: 8px; font-size: 13px; color: var(--text-muted);">${data.ai_analysis || ''}</div>
            </div>
          `;
        } else {
          resultDiv.innerHTML = `<div style="padding: 16px;">${data.analysis || 'Không tìm thấy voucher phù hợp'}</div>`;
        }
      } else {
        resultDiv.innerHTML = `<div style="padding: 16px; color: var(--text-muted);">${data.error}</div>`;
      }
    } catch (err) {
      resultDiv.innerHTML = '<div style="padding: 16px; color: var(--text-muted);">Lỗi kết nối</div>';
    }
  },

  /* ─── DEAL FINDER ─── */
  showDealFinder() {
    document.getElementById('modal-overlay').classList.add('open');
    document.getElementById('modal-title').textContent = '🔥 Tìm Deal Siêu Hời';
    document.getElementById('modal-body').innerHTML = `
      <div class="form-group">
        <label>Nhập sản phẩm bạn muốn tìm deal</label>
        <input type="text" id="deal-query" placeholder="VD: Điện thoại Samsung dưới 5 triệu" class="input">
      </div>
      <div class="form-actions">
        <button class="btn btn-secondary" onclick="App.closeModal()">Đóng</button>
        <button class="btn btn-primary" onclick="App.findDeal()">🔍 Tìm deal</button>
      </div>
      <div id="deal-result" class="mt-16"></div>
    `;
    document.getElementById('deal-query').focus();
  },

  async findDeal() {
    const query = document.getElementById('deal-query').value.trim();
    if (!query) {
      this.showToast('Vui lòng nhập sản phẩm', 'error');
      return;
    }

    const resultDiv = document.getElementById('deal-result');
    resultDiv.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';

    try {
      const response = await fetch('/api/find-deal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await response.json();

      if (data.success) {
        let html = data.result
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\n/g, '<br>');
        resultDiv.innerHTML = `<div style="background: var(--bg-secondary); padding: 16px; border-radius: var(--radius); line-height: 1.6;">${html}</div>`;
      } else {
        resultDiv.innerHTML = `<div style="color: var(--text-muted);">${data.error}</div>`;
      }
    } catch (err) {
      resultDiv.innerHTML = '<div style="color: var(--text-muted);">Lỗi kết nối</div>';
    }
  },

  /* ─── SETTINGS ─── */
  showSettings() {
    document.getElementById('modal-overlay').classList.add('open');
    document.getElementById('modal-title').textContent = '⚙️ Cài đặt';
    document.getElementById('modal-body').innerHTML = `
      <div style="margin-bottom: 16px;">
        <label style="display: flex; align-items: center; gap: 12px; cursor: pointer;">
          <span>🌙 Chế độ tối</span>
          <input type="checkbox" ${this.state.theme === 'dark' ? 'checked' : ''} onchange="App.toggleTheme()" style="width: 18px; height: 18px;">
        </label>
      </div>
      <div style="margin-bottom: 16px; padding: 16px; background: var(--bg-secondary); border-radius: var(--radius);">
        <div style="font-weight: 600; margin-bottom: 4px;">Về QT_SHOPEE AI</div>
        <div style="font-size: 13px; color: var(--text-muted);">
          Phiên bản 1.0<br>
          Trợ lý săn mã giảm giá & tìm deal thông minh<br>
          Powered by Google Gemini AI
        </div>
      </div>
      <div class="form-actions">
        <button class="btn btn-primary" onclick="App.closeModal()">Đóng</button>
      </div>
    `;
  },

  /* ─── MODAL ─── */
  closeModal() {
    document.getElementById('modal-overlay').classList.remove('open');
  },

  /* ─── TOAST ─── */
  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  },

  /* ─── UTILITY ─── */
  escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
};

// ─── INIT ───
document.addEventListener('DOMContentLoaded', () => App.init());

// Close modal on overlay click
document.getElementById('modal-overlay').addEventListener('click', (e) => {
  if (e.target === e.currentTarget) App.closeModal();
});
