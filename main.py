#!/usr/bin/env python
import os
import sys
import subprocess
import time
import math
import html as pyhtml
from pathlib import Path
import streamlit as st

# --- CÀI ĐẶT HỆ THỐNG ---
def install_playwright_browsers():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception: pass

if not os.path.exists("config.toml"):
    with open("config.toml", "w", encoding="utf-8") as f:
        f.write('[reddit]\nclient_id = "dummy"\nclient_secret = "dummy"\nusername = "dummy"\npassword = "dummy"\nuser_agent = "dummy"\n')

from playwright.sync_api import sync_playwright

try:
    from threads_scraper import get_threads_content
    from video_creation.background import chop_background, get_background_config
    from video_creation.final_video import make_final_video
    from video_creation.voices import save_text_to_mp3
except Exception: pass

BANNER = """
██████╗ ██╗   ██╗ █████╗ ███╗   ██╗ ██████╗ 
██╔═══██╗██║   ██║██╔══██╗████╗  ██║██╔════╝ 
██║   ██║██║   ██║███████║██╔██╗ ██║██║  ███╗
██║██╗██║██║   ██║██╔══██║██║╚██╗██║██║   ██║
╚██████╔╝╚██████╔╝██║  ██║██║ ╚████║╚██████╔╝
 ╚═██╔═╝  ╚═════╝  ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ 
"""

# --- GIAO DIỆN THREADS SIÊU ĐẸP ---
def tao_anh_giao_dien_threads_gia(text):
    os.makedirs("assets/temp/png", exist_ok=True)
    with sync_playwright() as p:
        install_playwright_browsers()
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(device_scale_factor=3) # Tăng độ nét lên x3
        
        # Xử lý text để không bị lỗi HTML
        safe_text = pyhtml.escape(text).replace('\n', '<br>')

        # Code HTML/CSS làm giao diện cực xịn xò, nền trong suốt
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="background: transparent; margin: 0; display: flex; justify-content: center; align-items: center; padding: 20px;">
            <div id="card" style="background: rgba(24, 24, 24, 0.85); border: 1px solid #444; border-radius: 25px; padding: 40px; color: white; width: 850px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; box-shadow: 0 15px 35px rgba(0,0,0,0.6); backdrop-filter: blur(10px);">
                <div style="display: flex; align-items: center; margin-bottom: 25px;">
                    <img src="https://ui-avatars.com/api/?name=Quang+ICTU&background=random&size=120" style="width: 80px; height: 80px; border-radius: 50%; margin-right: 20px;">
                    <div>
                        <div style="font-weight: bold; font-size: 32px; display: flex; align-items: center; gap: 8px;">Quang ICTU <span style="color: #1d9bf0; font-size: 28px;">✔</span></div>
                        <div style="color: #888; font-size: 24px;">@quang_deptrai</div>
                    </div>
                </div>
                <div style="font-size: 38px; line-height: 1.5; margin-bottom: 30px;">
                    {safe_text}
                </div>
                <div style="color: #888; font-size: 26px; display: flex; gap: 40px; border-top: 1px solid #444; padding-top: 20px;">
                    <span>❤️ 15.2 N</span>
                    <span>💬 843</span>
                    <span>🔁 2.1 N</span>
                </div>
            </div>
        </body>
        </html>
        """
        page.set_content(html_content)
        # omit_background=True LÀ CHÌA KHÓA: Nó làm nền trong suốt để lộ Minecraft ra!
        page.locator("#card").screenshot(path="assets/temp/png/title.png", omit_background=True)
        browser.close()

def run_process(url):
    with st.status("🎬 Đang tạo video... Cùng đón chờ siêu phẩm!", expanded=True) as status:
        st.write("🛠️ Đang kiểm tra hệ thống...")
        install_playwright_browsers()
        
        st.write("📡 Đang cào dữ liệu Threads...")
        text = get_threads_content(url)
        if not text:
            st.error("Lỗi: Không lấy được nội dung!")
            return

        reddit_obj = {"thread_id": str(int(time.time())), "thread_title": text, "thread_post": "", "comments": []}

        st.write("🎙️ Đang tạo giọng AI...")
        length, _ = save_text_to_mp3(reddit_obj)
        
        st.write("📸 Đang dựng ảnh giao diện chuẩn Threads...")
        tao_anh_giao_dien_threads_gia(text)

        st.write("🎞️ Đang xử lý video nền...")
        bg_config = {"video": get_background_config("video"), "audio": get_background_config("audio")}
        
        success = chop_background(bg_config, math.ceil(length), reddit_obj)

        if success:
            st.write("🚀 Đang Render video cuối cùng...")
            make_final_video(0, math.ceil(length), reddit_obj, bg_config)
            status.update(label="✅ Xong rồi Quang ơi! Xem ngay thành quả!", state="complete")
            
            vids = sorted(Path("video_output").glob("*.mp4"), key=os.path.getmtime)
            if vids: st.video(str(vids[-1]))
        else:
            status.update(label="❌ Lỗi xử lý video nền!", state="error")

# --- GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="Threads Bot - Quang ICTU")
st.title("🧵 Threads Video Maker")
st.markdown(f"```\n{BANNER}\n```")
st.subheader("Dự án của Quang - ICTU (Bản Đẹp Không Tì Vết)")

st.markdown("### 1️⃣ Tải video nền (Minecraft/Parkour...)")
uploaded_video = st.file_uploader("📂 Chọn file .mp4 của bạn", type=["mp4"])

if uploaded_video:
    video_dir = Path("assets/backgrounds/video")
    video_dir.mkdir(parents=True, exist_ok=True)
    for f in video_dir.glob("*.mp4"):
        try: os.remove(f)
        except: pass
    save_path = video_dir / uploaded_video.name
    with open(save_path, "wb") as f:
        f.write(uploaded_video.getbuffer())
    st.success(f"✅ Đã tải lên file: {uploaded_video.name}.")

st.markdown("### 2️⃣ Dán link Threads")
link = st.text_input("🔗 Dán link Threads vào đây:")

if st.button("Bắt đầu làm Video"):
    if not uploaded_video: st.error("⚠️ Quang ơi, upload video nền ở Bước 1 trước đã nhé!")
    elif not link.strip(): st.warning("⚠️ Quang chưa nhập link kìa!")
    else: run_process(link.strip())