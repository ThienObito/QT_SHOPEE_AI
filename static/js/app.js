/* ═══════════════════════════════════════════════
   QTDEAL.AI — Frontend Application v2.0
   ═══════════════════════════════════════════════ */

marked.setOptions({
  breaks: true,
  gfm: true,
  highlight: (code, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      try { return hljs.highlight(code, { language: lang }).value; }
      catch (e) { /* fall through */ }
    }
    try { return hljs.highlightAuto(code).value; }
    catch (e) { return code; }
  }
});

const App = {
  state: {
    view: 'home',
    theme: localStorage.getItem('qtdeat-theme') || 'light',
    currentChatId: null,
    isStreaming: false,
    chats: [],
    coupons: [],
    sidebarOpen: false,
  },

  /* ═══ INIT ═══ */
  init() {
    this.applyTheme();
    this.loadChats();
    this.loadCoupons();
    this.bindEvents();
    this.autoResize();
  },

  /* ═══ THEME ═══ */
  applyTheme() {
    if (this.state.theme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
      document.querySelector('.theme-sun').style.display = 'none';
      document.querySelector('.theme-moon').style.display = 'block';
    }
    const cb = document.getElementById('dark-toggle');
    if (cb) cb.checked = this.state.theme === 'dark';
  },

  toggleTheme() {
    this.state.theme = this.state.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('qtdeat-theme', this.state.theme);
    this.applyTheme();
  },

  /* ═══ VIEWS ═══ */
  showView(name) {
    // Hide all views (use display:none)
    ['view-home', 'view-chat', 'view-vouchers', 'view-settings'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.style.display = id === `view-${name}` ? '' : 'none';
    });
    // Results view
    const rv = document.getElementById('view-results');
    if (rv) rv.style.display = 'none';

    this.state.view = name;
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const navMap = { home: 0, chat: 1, vouchers: 2, settings: 3 };
    const items = document.querySelectorAll('.nav-item');
    if (items[navMap[name]]) items[navMap[name]].classList.add('active');

    this.closeSidebar();
  },

  /* ═══ SIDEBAR ═══ */
  closeSidebar() {
    if (window.innerWidth <= 768) {
      this.state.sidebarOpen = false;
      document.querySelector('.sidebar').classList.remove('open');
    }
  },

  /* ═══ SEARCH ═══ */
  async doSearch(query) {
    if (!query.trim()) return;

    document.getElementById('view-home').style.display = 'none';
    const rv = document.getElementById('view-results');
    rv.style.display = '';
    document.getElementById('results-query').textContent = `🔍 ${query}`;
    document.getElementById('results-meta').textContent = '🔎 Đang tìm sản phẩm thật từ Shopee...';
    document.getElementById('search-result-ai').innerHTML = '<div class="typing-dots"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>';

    try {
      // Step 1: Search Shopee for real products
      const res = await fetch('/api/shop-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await res.json();

      if (data.success && data.products && data.products.length > 0) {
        const products = data.products.filter(p => !p.filtered);
        document.getElementById('results-meta').textContent =
          `🏆 Tìm thấy ${products.length} sản phẩm từ Shopee | AI Deal Score`;

        // Render product cards
        document.getElementById('search-result-ai').innerHTML =
          '<div class="product-grid" id="product-grid"></div>';

        const grid = document.getElementById('product-grid');
        products.forEach((p, i) => {
          const score = p.deal_score || 0;
          const isHot = score >= 70;
          const grid = document.getElementById('product-grid');
          const card = document.createElement('div');
          card.className = 'product-card';
          card.innerHTML = `
            ${isHot ? '<div class="product-card-badge">🔥 TOP DEAL</div>' : ''}
            <div class="product-card-img">📱</div>
            <div class="product-card-name">${this.esc(p.name)}</div>
            <div class="product-card-shop">
              ${this.esc(p.shop || '')}
              ${p.shop_type ? `<span style="margin-left:6px;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;background:${p.shop_type==='Mall'?'var(--orange-400)':'var(--bg-muted)'};color:${p.shop_type==='Mall'?'white':'var(--text-secondary)'}">${p.shop_type}</span>` : ''}
            </div>
            <div class="product-card-price-row">
              <span class="product-card-price">${Number(p.price).toLocaleString()}₫</span>
              ${p.original_price && p.original_price > p.price ? `<span class="product-card-price-original">${Number(p.original_price).toLocaleString()}₫</span>` : ''}
              ${p.discount_percent ? `<span class="product-card-discount">-${p.discount_percent}%</span>` : ''}
            </div>
            ${p.vouchers && p.vouchers.length ? `<div class="product-card-voucher">🎫 ${p.vouchers.slice(0,2).join(' • ')}</div>` : ''}
            <div class="product-card-savings">
              ⭐ ${p.rating || '?'} ★ | Đã bán ${p.sold || 0}
              ${p.final_price && p.final_price < p.price ? `<span style="margin-left:auto;color:var(--primary)">💰 ${Number(p.price - p.final_price).toLocaleString()}₫</span>` : ''}
            </div>
            <div style="margin-top:10px;display:flex;gap:8px;">
              <div style="flex:1;height:4px;background:var(--bg-muted);border-radius:2px;overflow:hidden;">
                <div style="width:${Math.min(score,100)}%;height:100%;background:${score >= 70 ? 'linear-gradient(90deg,#16a34a,#22c55e)' : score >= 50 ? 'linear-gradient(90deg,#f97316,#fb923c)' : 'linear-gradient(90deg,#ef4444,#f87171)'};border-radius:2px;"></div>
              </div>
              <span style="font-size:11px;font-weight:600;color:${score >= 70 ? '#16a34a' : score >= 50 ? '#f97316' : '#ef4444'}">Deal ${score}</span>
            </div>
            ${p.url ? `<a href="${this.esc(p.url)}" target="_blank" style="display:block;text-align:center;margin-top:10px;padding:8px;background:var(--orange-500);color:white;border-radius:var(--radius-sm);font-weight:600;font-size:13px;text-decoration:none;">${p.has_real_link ? '🛒 Mua ngay trên Shopee' : '🔍 Xem trên Shopee'}</a>` : ''}
          `;
          if (grid) grid.appendChild(card);
        });

        // Step 2: AI analysis (optional, runs in parallel)
        fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: `Phân tích các sản phẩm sau từ Shopee cho "${query}". Đưa ra lời khuyên mua hàng, so sánh giá, đề xuất voucher phù hợp. Trả lời ngắn gọn bằng tiếng Việt.\n\nSản phẩm:\n${products.map((p,i) => `${i+1}. ${p.name} - ${Number(p.price).toLocaleString()}₫ (giảm ${p.discount_percent||0}%) - Shop: ${p.shop||'?'} - Sao: ${p.rating||'?'}`).join('\n')}` })
        }).then(r => r.json()).then(d => {
          if (d.success) {
            const analysisDiv = document.createElement('div');
            analysisDiv.className = 'search-result-ai';
            analysisDiv.style.marginTop = '24px';
            analysisDiv.innerHTML = `<div class="result-content"><div style="font-weight:600;margin-bottom:8px;">🤖 Phân tích của AI:</div>${marked.parse(d.answer)}</div>`;
            document.getElementById('view-results').appendChild(analysisDiv);
            analysisDiv.querySelectorAll('pre code').forEach(b => hljs.highlightElement(b));
          }
        }).catch(() => {});

      } else if (data.success && data.products) {
        // Fallback: show raw
        document.getElementById('results-meta').textContent = '📦 Kết quả tìm kiếm';
        const html = marked.parse(data.products[0]?.raw || 'Không tìm thấy sản phẩm phù hợp.');
        document.getElementById('search-result-ai').innerHTML = `<div class="result-content">${html}</div>`;
      } else {
        document.getElementById('results-meta').textContent = '❌ Không tìm thấy';
        document.getElementById('search-result-ai').innerHTML =
          `<div class="result-content" style="color:var(--text-tertiary)">${data.error || 'Không tìm thấy sản phẩm. Vui lòng thử từ khóa khác.'}</div>`;
      }
    } catch(err) {
      document.getElementById('results-meta').textContent = '❌ Lỗi kết nối';
      document.getElementById('search-result-ai').innerHTML =
        '<div class="result-content" style="color:#ef4444;">Lỗi kết nối đến server. Vui lòng thử lại.</div>';
    }

    document.getElementById('search-input').blur();
  },

  /* ═══ CHAT ═══ */
  async sendChat() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg || this.state.isStreaming) return;

    input.value = '';
    input.style.height = 'auto';
    this.state.isStreaming = true;
    document.getElementById('chat-send').disabled = true;

    // Add user msg
    this.addMsg('user', msg);

    // Show typing
    const container = document.getElementById('chat-msgs-inner');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing';
    typingDiv.id = 'typing-el';
    typingDiv.innerHTML = '<div class="msg-avatar" style="background:var(--bg-muted);color:var(--text-primary);font-size:12px;">AI</div><div class="typing-dots"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>';
    container.appendChild(typingDiv);
    this.scrollChat();

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, chat_id: this.state.currentChatId })
      });
      const data = await res.json();

      document.getElementById('typing-el')?.remove();

      if (data.success) {
        this.state.currentChatId = data.chat_id;
        this.addMsg('assistant', data.answer);
        this.loadChats();
      } else {
        this.toast(data.error || 'Lỗi xử lý', 'error');
      }
    } catch(err) {
      document.getElementById('typing-el')?.remove();
      this.toast('Lỗi kết nối', 'error');
    }

    this.state.isStreaming = false;
    document.getElementById('chat-send').disabled = false;
    input.focus();
  },

  addMsg(role, content) {
    const container = document.getElementById('chat-msgs-inner');
    const div = document.createElement('div');
    div.className = `msg ${role}`;
    const avatar = role === 'user' ? '👤' : '🤖';
    const html = marked.parse(content);
    div.innerHTML = `<div class="msg-avatar">${avatar}</div><div class="msg-body">${html}</div>`;
    container.appendChild(div);
    this.scrollChat();
    // Highlight code
    div.querySelectorAll('pre code').forEach(b => hljs.highlightElement(b));
  },

  scrollChat() {
    requestAnimationFrame(() => {
      document.getElementById('chat-messages').scrollTop = 999999;
    });
  },

  /* ═══ CHAT HISTORY ═══ */
  async loadChats() {
    try {
      const res = await fetch('/api/chats');
      const data = await res.json();
      if (data.success) this.state.chats = data.chats;
      this.renderChats();
    } catch(e) { /* silent */ }
  },

  renderChats() {
    const list = document.getElementById('chat-list');
    if (!list) return;
    if (!this.state.chats.length) {
      list.innerHTML = '<div class="chat-list-empty"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.4"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg><span>Chưa có lịch sử</span></div>';
      return;
    }
    list.innerHTML = this.state.chats.map(c => `
      <button class="chat-item ${c.id === this.state.currentChatId ? 'active' : ''}" data-id="${c.id}">
        <span class="chat-title">${this.esc(c.title)}</span>
        <span class="chat-del" data-id="${c.id}" onclick="event.stopPropagation();App.delChat('${c.id}')">✕</span>
      </button>
    `).join('');
    list.querySelectorAll('.chat-item:not(.chat-del)').forEach(el => {
      el.addEventListener('click', () => this.loadChat(el.dataset.id));
    });
  },

  async loadChat(id) {
    try {
      const res = await fetch(`/api/chats/${id}`);
      const data = await res.json();
      if (data.success) {
        this.state.currentChatId = id;
        const container = document.getElementById('chat-msgs-inner');
        container.innerHTML = '';
        data.messages.forEach(m => this.addMsg(m.role, m.content));
        this.showView('chat');
        this.renderChats();
      }
    } catch(e) { this.toast('Lỗi tải chat', 'error'); }
  },

  newChat() {
    this.state.currentChatId = null;
    const container = document.getElementById('chat-msgs-inner');
    container.innerHTML = `<div style="text-align:center;padding:60px 20px;color:var(--text-tertiary);font-size:14px;">
      <div style="font-size:40px;margin-bottom:12px;">🤖</div>
      <div style="font-weight:600;color:var(--text-secondary);margin-bottom:4px;">QTDEAL.AI Chat</div>
      <div>Tôi là AI chuyên săn deal và tìm mã giảm giá.</div>
      <div style="margin-top:12px;font-size:13px;">Hãy hỏi tôi bất cứ điều gì về mua sắm!</div>
    </div>`;
    this.showView('chat');
    document.getElementById('chat-input').focus();
  },

  async delChat(id) {
    try {
      await fetch(`/api/chats/${id}`, { method: 'DELETE' });
      if (this.state.currentChatId === id) this.newChat();
      else this.loadChats();
    } catch(e) { this.toast('Lỗi xóa', 'error'); }
  },

  /* ═══ VOUCHER CENTER ═══ */
  async loadCoupons() {
    try {
      const res = await fetch('/api/coupon/list?active_only=true');
      const data = await res.json();
      if (data.success) this.state.coupons = data.coupons;
      this.renderCoupons('all');
    } catch(e) { /* silent */ }
  },

  renderCoupons(platform) {
    const list = document.getElementById('voucher-list');
    if (!list) return;

    let filtered = this.state.coupons;
    if (platform !== 'all') {
      filtered = filtered.filter(c => c.platform === platform);
    }

    if (!filtered.length) {
      list.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-tertiary);"><div style="font-size:32px;margin-bottom:8px;">🎫</div><div>Chưa có mã giảm giá nào</div></div>';
      return;
    }

    list.innerHTML = filtered.map(c => {
      const icon = c.platform === 'shopee' ? '🛒' : c.platform === 'lazada' ? '🟣' : c.platform === 'tiktok' ? '🎵' : '🔵';
      const value = c.discount_type === 'percent' ? `-${c.discount_value}%` : `-${Number(c.discount_value).toLocaleString()}₫`;
      const min = c.min_order > 0 ? `Đơn từ ${Number(c.min_order).toLocaleString()}₫` : '';
      return `
        <div class="voucher-card">
          <div class="voucher-card-left">
            <div class="voucher-card-icon ${c.platform}">${icon}</div>
            <div class="voucher-card-info">
              <div class="voucher-card-code">${this.esc(c.code)}</div>
              <div class="voucher-card-desc">${this.esc(c.description || min)}</div>
            </div>
          </div>
          <div class="voucher-card-right">
            <div>
              <div class="voucher-card-value">${value}</div>
              <div class="voucher-card-min">${min}</div>
            </div>
            <button class="btn-copy" data-code="${this.esc(c.code)}">Sao chép</button>
          </div>
        </div>`;
    }).join('');

    // Copy buttons
    list.querySelectorAll('.btn-copy').forEach(btn => {
      btn.addEventListener('click', async () => {
        const code = btn.dataset.code;
        try {
          await navigator.clipboard.writeText(code);
          btn.textContent = '✅ Đã copy';
          btn.classList.add('copied');
          setTimeout(() => { btn.textContent = 'Sao chép'; btn.classList.remove('copied'); }, 2000);
        } catch(e) {
          // Fallback
          const ta = document.createElement('textarea');
          ta.value = code;
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          ta.remove();
          btn.textContent = '✅ Đã copy';
          btn.classList.add('copied');
          setTimeout(() => { btn.textContent = 'Sao chép'; btn.classList.remove('copied'); }, 2000);
        }
      });
    });
  },

  /* ═══ MODAL ═══ */
  openModal(title, bodyHTML) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = bodyHTML;
    document.getElementById('modal-overlay').classList.add('open');
  },
  closeModal() {
    document.getElementById('modal-overlay').classList.remove('open');
  },

  /* ═══ TOAST ═══ */
  toast(msg, type = 'info') {
    const c = document.getElementById('toast-container');
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.textContent = msg;
    c.appendChild(t);
    setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 300); }, 2800);
  },

  /* ═══ UTILITY ═══ */
  esc(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
  },

  /* ═══ EVENTS ═══ */
  bindEvents() {
    // Nav items
    document.querySelectorAll('.nav-item[data-view]').forEach(el => {
      el.addEventListener('click', () => {
        const view = el.dataset.view;
        if (view === 'chat') this.newChat();
        else this.showView(view);
      });
    });

    // Hero search
    document.getElementById('search-form').addEventListener('submit', (e) => {
      e.preventDefault();
      this.doSearch(document.getElementById('search-input').value);
    });

    // Trending chips
    document.querySelectorAll('.trend-chip').forEach(el => {
      el.addEventListener('click', () => {
        document.getElementById('search-input').value = el.dataset.query;
        this.doSearch(el.dataset.query);
      });
    });

    // Chat form
    document.getElementById('chat-form').addEventListener('submit', (e) => {
      e.preventDefault();
      this.sendChat();
    });
    document.getElementById('chat-input').addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendChat();
      }
    });

    // New chat button
    document.getElementById('new-chat-btn').addEventListener('click', () => this.newChat());

    // Theme
    document.getElementById('theme-toggle').addEventListener('click', () => this.toggleTheme());
    const dt = document.getElementById('dark-toggle');
    if (dt) {
      dt.addEventListener('change', () => this.toggleTheme());
    }

    // Hamburger
    document.getElementById('hamburger').addEventListener('click', () => {
      this.state.sidebarOpen = !this.state.sidebarOpen;
      document.querySelector('.sidebar').classList.toggle('open');
    });

    // Close sidebar on content click (mobile)
    document.querySelector('.main-content').addEventListener('click', () => this.closeSidebar());

    // Modal overlay click
    document.getElementById('modal-overlay').addEventListener('click', (e) => {
      if (e.target === e.currentTarget) this.closeModal();
    });

    // Voucher tabs
    document.querySelectorAll('.voucher-tab').forEach(el => {
      el.addEventListener('click', () => {
        document.querySelectorAll('.voucher-tab').forEach(t => t.classList.remove('active'));
        el.classList.add('active');
        this.renderCoupons(el.dataset.platform);
      });
    });

    // View all deals
    document.getElementById('view-all-deals')?.addEventListener('click', () => {
      this.showView('chat');
    });
  },

  autoResize() {
    ['chat-input', 'message-input'].forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.addEventListener('input', () => {
          el.style.height = 'auto';
          el.style.height = Math.min(el.scrollHeight, 120) + 'px';
        });
      }
    });
  }
};

// ─── DOM READY ───
document.addEventListener('DOMContentLoaded', () => App.init());
