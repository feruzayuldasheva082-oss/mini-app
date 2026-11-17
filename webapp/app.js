const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
if (tg) { try { tg.ready(); tg.expand(); } catch (e) {} }

const state = {
  menu: [],
  cart: {}, // id -> qty
  user: tg && tg.initDataUnsafe && tg.initDataUnsafe.user ? tg.initDataUnsafe.user : null,
};
// Telegram ichida user.id bo'ladi; oddiy brauzerda test qilish uchun localStorage dan doimiy sun'iy ID ishlatamiz.
state.userId = (function () {
  if (state.user && state.user.id) return state.user.id;
  let id = null;
  try { id = Number(localStorage.getItem("hdm_client_id")); } catch (e) {}
  if (!id || id >= 0) {
    id = -Math.floor(Math.random() * 1000000000) - 1;
    try { localStorage.setItem("hdm_client_id", String(id)); } catch (e) {}
  }
  return id;
})();

const views = ["home", "menu", "checkout", "orders", "success"];
const params = new URLSearchParams(window.location.search);
const requestedView = params.get("view");

function $(sel) { return document.querySelector(sel); }
function showView(name) {
  views.forEach(v => {
    const el = document.getElementById(`view-${v}`);
    if (el) el.classList.toggle("active", v === name);
  });
  const bar = document.getElementById("cart-bar");
  if (bar) bar.classList.toggle("show", name === "menu" && cartCount() > 0);
  if (name === "home") { $("#page-title").textContent = "Hot Dog Mafia’ga xush kelibsiz!"; $("#page-subtitle").textContent = "Mazali hot-doglar. Tez va qulay buyurtma."; }
  if (name === "orders") loadOrders();
  window.scrollTo(0, 0);
}

function formatSum(n) { return (n || 0).toLocaleString("uz-UZ") + " so‘m"; }
function toast(msg) {
  const t = $("#toast"); if (!t) return;
  t.textContent = msg; t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2200);
}

async function api(path, opts = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
  if (!res.ok) throw new Error(await res.text() || res.statusText);
  return res.json();
}

async function loadMenu() {
  try {
    state.menu = await api("/api/menu");
    renderMenu();
  } catch (e) {
    $("#menu-list").innerHTML = `<div class="empty">Menyuni yuklab bo‘lmadi.</div>`;
  }
}

function cartCount() { return Object.values(state.cart).reduce((a,b)=>a+b,0); }
function cartTotal() {
  let t = 0;
  for (const [id, qty] of Object.entries(state.cart)) {
    const item = state.menu.find(m => m.id == id);
    if (item) t += item.price * qty;
  }
  return t;
}
function updateCartUI() {
  $("#cart-summary").textContent = `${cartCount()} ta · ${formatSum(cartTotal())}`;
  const bar = document.getElementById("cart-bar");
  if (bar) bar.classList.toggle("show", document.getElementById("view-menu").classList.contains("active") && cartCount() > 0);
}
function changeQty(id, delta) {
  const cur = state.cart[id] || 0;
  const next = cur + delta;
  if (next <= 0) delete state.cart[id]; else state.cart[id] = next;
  renderMenu();
  updateCartUI();
}

function renderMenu() {
  const list = $("#menu-list");
  if (!state.menu.length) { list.innerHTML = `<div class="empty">Menyu hozircha bo‘sh.</div>`; return; }
  const groups = {};
  state.menu.forEach(m => { (groups[m.category] = groups[m.category] || []).push(m); });
  let html = "";
  for (const [cat, items] of Object.entries(groups)) {
    html += `<div class="muted" style="font-weight:700;margin-top:4px;">${cat}</div>`;
    for (const m of items) {
      const qty = state.cart[m.id] || 0;
      html += `<div class="card menu-card">
        <div class="menu-head"><div><div class="menu-name">${escapeHtml(m.name)}</div><div class="menu-desc">${escapeHtml(m.description||"")}</div></div><div class="price">${formatSum(m.price)}</div></div>
        <div class="qty-row">
          <button class="qty-btn" data-dec="${m.id}">−</button>
          <span class="qty">${qty}</span>
          <button class="qty-btn" data-inc="${m.id}">+</button>
        </div>
      </div>`;
    }
  }
  list.innerHTML = html;
  list.querySelectorAll("[data-inc]").forEach(b => b.onclick = () => changeQty(Number(b.dataset.inc), 1));
  list.querySelectorAll("[data-dec]").forEach(b => b.onclick = () => changeQty(Number(b.dataset.dec), -1));
}

function escapeHtml(s){ return String(s).replace(/[&<>"']/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c])); }

function openCheckout() {
  if (cartCount() === 0) { toast("Savat bo‘sh"); return; }
  const items = [];
  for (const [id, qty] of Object.entries(state.cart)) {
    const m = state.menu.find(x => x.id == id);
    if (m) items.push({ ...m, qty });
  }
  $("#checkout-items").innerHTML = items.map(i => `<div class="order-item"><span>${escapeHtml(i.name)} × ${i.qty}</span><span>${formatSum(i.price*i.qty)}</span></div>`).join("");
  $("#checkout-total").textContent = formatSum(cartTotal());
  if (state.user) {
    const name = [state.user.first_name, state.user.last_name].filter(Boolean).join(" ");
    const nameInput = document.querySelector('input[name="full_name"]');
    if (nameInput && !nameInput.value) nameInput.value = name;
  }
  showView("checkout");
}

function statusLabel(s) {
  const map = { new: "Yangi", accepted: "Qabul qilindi", cooking: "Tayyorlanmoqda", delivering: "Yetkazilmoqda", done: "Yakunlandi", cancelled: "Bekor qilindi" };
  return map[s] || s;
}

async function loadOrders() {
  const list = $("#orders-list");
  list.innerHTML = `<div class="empty">Yuklanmoqda...</div>`;
  try {
    const orders = await api(`/api/orders?user_id=${encodeURIComponent(state.userId)}`);
    if (!orders.length) { list.innerHTML = `<div class="empty">Hozircha buyurtmalar yo‘q.</div>`; return; }
    list.innerHTML = orders.map(o => {
      const items = (o.items||[]).map(i => `${escapeHtml(i.name)} × ${i.qty}`).join(", ");
      const date = o.created_at ? new Date(o.created_at*1000).toLocaleString() : "";
      return `<div class="card">
        <div style="display:flex;justify-content:space-between;gap:8px;align-items:center;"><strong>#${o.id}</strong><span class="status ${o.status}">${statusLabel(o.status)}</span></div>
        <div class="muted" style="margin-top:4px;">${date}</div>
        <div style="margin-top:6px;font-size:14px;">${items}</div>
        <div style="margin-top:6px;font-weight:700;">${formatSum(o.total)}</div>
      </div>`;
    }).join("");
  } catch (e) {
    list.innerHTML = `<div class="empty">Buyurtmalarni yuklab bo‘lmadi.</div>`;
  }
}

async function submitOrder(e) {
  e.preventDefault();
  if (cartCount() === 0) { toast("Savat bo‘sh"); return; }
  const form = e.target;
  const items = [];
  for (const [id, qty] of Object.entries(state.cart)) {
    const m = state.menu.find(x => x.id == id);
    if (m) items.push({ id: m.id, name: m.name, price: m.price, qty });
  }
  const payload = {
    user_id: state.userId,
    username: state.user ? (state.user.username || null) : null,
    full_name: form.full_name.value.trim(),
    phone: form.phone.value.trim(),
    address: form.address.value.trim(),
    comment: form.comment.value.trim(),
    items,
    total: cartTotal(),
  };
  try {
    const res = await api("/api/orders", { method: "POST", body: JSON.stringify(payload) });
    state.cart = {};
    updateCartUI();
    renderMenu();
    form.reset();
    $("#success-text").textContent = `Buyurtma #${res.id} qabul qilindi. Holatini “Mening buyurtmalarim” bo‘limidan kuzatishingiz mumkin.`;
    showView("success");
  } catch (err) {
    toast("Xatolik yuz berdi. Qayta urinib ko‘ring.");
  }
}

document.addEventListener("click", (e) => {
  const nav = e.target.closest("[data-nav]");
  if (nav) showView(nav.dataset.nav);
});
$("#checkout-btn").addEventListener("click", openCheckout);
$("#checkout-form").addEventListener("submit", submitOrder);

loadMenu();
updateCartUI();
showView(views.includes(requestedView) && requestedView !== "success" ? requestedView : "home");
