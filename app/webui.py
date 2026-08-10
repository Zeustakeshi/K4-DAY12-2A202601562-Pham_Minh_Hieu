"""Giao diện demo tĩnh cho /chat — KHÔNG thuộc phạm vi chấm điểm của lab.

Trang HTML/CSS/JS đơn giản, tự chứa (không phụ thuộc CDN ngoài), gọi thẳng
vào /chat bằng fetch() ngay trên cùng domain nên không vướng CORS.
"""

from __future__ import annotations

INDEX_HTML = """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Day 12 Chat Service — Demo</title>
<style>
  :root {
    color-scheme: light dark;
    --bg: #0f1115; --panel: #171a21; --border: #2a2f3a;
    --text: #e8eaed; --muted: #9aa4b2; --accent: #6ea8fe;
    --user-bubble: #2b3446; --assistant-bubble: #1d2430; --err: #ff6b6b;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    background: var(--bg); color: var(--text);
    display: flex; flex-direction: column; height: 100vh;
  }
  header {
    padding: 14px 20px; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: 10px;
  }
  header h1 { font-size: 16px; margin: 0; font-weight: 600; }
  header .badge {
    font-size: 12px; color: var(--muted); border: 1px solid var(--border);
    border-radius: 999px; padding: 2px 10px;
  }
  .layout { flex: 1; display: flex; overflow: hidden; }
  aside {
    width: 280px; padding: 16px; border-right: 1px solid var(--border);
    display: flex; flex-direction: column; gap: 12px; overflow-y: auto;
  }
  aside label { font-size: 12px; color: var(--muted); display: block; margin-bottom: 4px; }
  aside input {
    width: 100%; padding: 8px 10px; border-radius: 8px; border: 1px solid var(--border);
    background: var(--panel); color: var(--text); font-size: 13px;
  }
  aside button {
    padding: 8px 10px; border-radius: 8px; border: 1px solid var(--border);
    background: var(--panel); color: var(--text); cursor: pointer; font-size: 13px;
  }
  aside button:hover { border-color: var(--accent); }
  #status { font-size: 12px; color: var(--muted); white-space: pre-wrap; }
  main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
  #messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
  .msg { max-width: 70%; padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.45; white-space: pre-wrap; }
  .msg.user { align-self: flex-end; background: var(--user-bubble); }
  .msg.assistant { align-self: flex-start; background: var(--assistant-bubble); }
  .msg.error { align-self: flex-start; background: transparent; border: 1px solid var(--err); color: var(--err); }
  .meta { font-size: 11px; color: var(--muted); margin-top: 4px; }
  form { display: flex; gap: 10px; padding: 16px 20px; border-top: 1px solid var(--border); }
  form input {
    flex: 1; padding: 12px 14px; border-radius: 10px; border: 1px solid var(--border);
    background: var(--panel); color: var(--text); font-size: 14px;
  }
  form button {
    padding: 12px 18px; border-radius: 10px; border: none; background: var(--accent);
    color: #06131f; font-weight: 600; cursor: pointer;
  }
  form button:disabled { opacity: .5; cursor: default; }
</style>
</head>
<body>
<header>
  <h1>💬 Day 12 Chat Service</h1>
  <span class="badge">demo UI — không phải phần chấm điểm</span>
</header>
<div class="layout">
  <aside>
    <div>
      <label for="token">API Token (Bearer)</label>
      <input id="token" type="password" placeholder="dán token của bạn" autocomplete="off">
    </div>
    <div>
      <label for="clientId">Client ID</label>
      <input id="clientId" type="text" value="web-demo">
    </div>
    <button id="checkBtn">Kiểm tra /healthz + /readyz</button>
    <button id="clearBtn">Xoá hội thoại</button>
    <div id="status"></div>
  </aside>
  <main>
    <div id="messages"></div>
    <form id="chatForm">
      <input id="messageInput" type="text" placeholder="Nhập tin nhắn..." autocomplete="off">
      <button id="sendBtn" type="submit">Gửi</button>
    </form>
  </main>
</div>
<script>
const messagesEl = document.getElementById("messages");
const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const tokenEl = document.getElementById("token");
const clientIdEl = document.getElementById("clientId");
const statusEl = document.getElementById("status");

function addMessage(role, text, meta) {
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.textContent = text;
  messagesEl.appendChild(div);
  if (meta) {
    const m = document.createElement("div");
    m.className = "meta";
    m.textContent = meta;
    div.appendChild(m);
  }
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

document.getElementById("clearBtn").addEventListener("click", () => {
  messagesEl.innerHTML = "";
});

document.getElementById("checkBtn").addEventListener("click", async () => {
  statusEl.textContent = "Đang kiểm tra...";
  try {
    const [h, r] = await Promise.all([
      fetch("/healthz").then((res) => res.json().then((j) => [res.status, j])),
      fetch("/readyz").then((res) => res.json().then((j) => [res.status, j])),
    ]);
    statusEl.textContent =
      "healthz " + h[0] + " " + JSON.stringify(h[1]) + "\\n" +
      "readyz  " + r[0] + " " + JSON.stringify(r[1]);
  } catch (err) {
    statusEl.textContent = "Lỗi: " + err;
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  const token = tokenEl.value.trim();
  if (!token) {
    addMessage("error", "Nhập API Token ở cột bên trái trước đã.");
    return;
  }

  addMessage("user", message);
  input.value = "";
  sendBtn.disabled = true;

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token,
        "X-Client-Id": clientIdEl.value.trim() || "web-demo",
      },
      body: JSON.stringify({ message }),
    });

    if (res.status === 401) {
      addMessage("error", "401 — token sai hoặc thiếu.");
    } else if (res.status === 429) {
      addMessage("error", "429 — gọi quá nhanh, thử lại sau " + (res.headers.get("Retry-After") || "?") + "s.");
    } else if (res.status === 402) {
      addMessage("error", "402 — đã vượt ngân sách chi phí trong ngày.");
    } else if (res.ok) {
      const data = await res.json();
      addMessage(
        "assistant",
        data.reply,
        "turns_before=" + data.turns_before + " · usd_cost=" + data.usd_cost
      );
    } else {
      addMessage("error", "Lỗi " + res.status + ": " + (await res.text()));
    }
  } catch (err) {
    addMessage("error", "Lỗi kết nối: " + err);
  } finally {
    sendBtn.disabled = false;
  }
});
</script>
</body>
</html>
"""
