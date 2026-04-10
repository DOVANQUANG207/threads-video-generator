#!/usr/bin/env python
import os
import sys
import subprocess
import time
import math
from pathlib import Path
import streamlit as st

# --- 1. TỰ ĐỘNG CÀI TRÌNH DUYỆT ---
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

def tao_anh_giao_dien_threads_gia(text):
    os.makedirs("assets/temp/png", exist_ok=True)
    with sync_playwright() as p:
        install_playwright_browsers()
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(device_scale_factor=2)
        html = f'<div style="background:#000; color:white; padding:50px; border-radius:30px; font-size:40px; text-align:center;">{text}</div>'
        page.set_content(html)
        page.locator("div").first.screenshot(path="assets/temp/png/title.png")
        browser.close()

def run_process(url):
    with st.status("🎬 Đang tạo video... Quang đợi tí nhé!", expanded=True) as status:
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
        
        st.write("📸 Đang dựng ảnh bài viết...")
        tao_anh_giao_dien_threads_gia(text)

        st.write("🎞️ Đang xử lý video nền...")
        bg_config = {"video": get_background_config("video"), "audio": get_background_config("audio")}
        
        success = chop_background(bg_config, math.ceil(length), reddit_obj)

        if success:
            st.write("🚀 Đang Render video cuối cùng...")
            make_final_video(0, math.ceil(length), reddit_obj, bg_config)
            status.update(label="✅ Xong rồi Quang ơi!", state="complete")
            
            vids = sorted(Path("video_output").glob("*.mp4"), key=os.path.getmtime)
            if vids: st.video(str(vids[-1]))
        else:
            status.update(label="❌ Lỗi xử lý video nền!", state="error")

# --- GIAO DIỆN ---
st.set_page_config(page_title="Threads Bot - Quang ICTU")
st.title("🧵 Threads Video Maker")
st.markdown(f"```\n{BANNER}\n```")
st.subheader("Dự án của Quang - ICTU")

link = st.text_input("🔗 Dán link Threads vào đây:")
if st.button("Bắt đầu làm Video"):
    if link.strip(): run_process(link.strip())
    else: st.warning("Quang chưa nhập link kìa!")