"""Giao diện chat thử nghiệm cho Day 12 Chat Service (FastAPI đã deploy).

Chạy local:
    streamlit run streamlit_app/app.py

Deploy Render (Web Service, runtime Python, KHÔNG dùng Dockerfile của service chính):
    Build Command: pip install -r streamlit_app/requirements.txt
    Start Command: streamlit run streamlit_app/app.py --server.port $PORT --server.address 0.0.0.0
"""

from __future__ import annotations

import requests
import streamlit as st

DEFAULT_API_URL = "https://day12-chat-fbw4.onrender.com"

st.set_page_config(page_title="Day 12 Chat Service — Demo", page_icon="💬")

if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.header("Cấu hình")
    api_url = st.text_input("API URL", value=DEFAULT_API_URL).rstrip("/")
    api_token = st.text_input("API Token (Bearer)", type="password")
    client_id = st.text_input("Client ID", value="streamlit-demo")

    st.divider()
    if st.button("Kiểm tra /healthz + /readyz"):
        try:
            healthz = requests.get(f"{api_url}/healthz", timeout=10)
            readyz = requests.get(f"{api_url}/readyz", timeout=10)
            st.success(f"/healthz {healthz.status_code} · /readyz {readyz.status_code}")
            st.json({"healthz": healthz.json(), "readyz": readyz.json()})
        except requests.RequestException as err:
            st.error(f"Không gọi được API: {err}")

    st.divider()
    if st.button("Xoá lịch sử hiển thị"):
        st.session_state.history = []
        st.rerun()

st.title("💬 Day 12 Chat Service — Demo")
st.caption("Giao diện thử nghiệm gọi thẳng vào API đã deploy (auth, rate limit, cost guard).")

for turn in st.session_state.history:
    with st.chat_message(turn["role"]):
        st.write(turn["content"])

prompt = st.chat_input("Nhập tin nhắn...")

if prompt:
    if not api_token:
        st.error("Nhập API Token ở sidebar trước đã — /chat yêu cầu Bearer token.")
        st.stop()

    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            response = requests.post(
                f"{api_url}/chat",
                json={"message": prompt},
                headers={
                    "Authorization": f"Bearer {api_token}",
                    "X-Client-Id": client_id,
                },
                timeout=30,
            )
        except requests.RequestException as err:
            placeholder.error(f"Lỗi kết nối: {err}")
            st.stop()

        if response.status_code == 401:
            placeholder.error("401 — token sai hoặc thiếu.")
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "?")
            placeholder.warning(f"429 — gọi quá nhanh, thử lại sau {retry_after}s.")
        elif response.status_code == 402:
            placeholder.warning("402 — đã vượt ngân sách chi phí trong ngày.")
        elif response.status_code == 200:
            data = response.json()
            reply = data["reply"]
            placeholder.write(reply)
            st.caption(
                f"turns_before={data['turns_before']} · "
                f"usd_cost={data['usd_cost']:.6f} · "
                f"usage={data['usage']}"
            )
            st.session_state.history.append({"role": "assistant", "content": reply})
        else:
            placeholder.error(f"Lỗi {response.status_code}: {response.text}")
