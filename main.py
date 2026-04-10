#!/usr/bin/env python
import os
import sys
import subprocess
import time
import math
from pathlib import Path

# --- 1. TỰ ĐỘNG CÀI TRÌNH DUYỆT (FIX LỖI EXECUTABLE) ---
def install_playwright_browsers():
    try:
        # Kiểm tra xem đã cài Chromium chưa, nếu chưa thì cài luôn
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception as e:
        print(f"⚠️ Lỗi cài trình duyệt: {e}")

# Giả lập config Reddit để không bị treo Terminal
if not os.path.exists("config.toml"):
    with open("config.toml", "w", encoding="utf-8") as f:
        f.write('[reddit]\nclient_id = "dummy"\nclient_secret = "dummy"\nusername = "dummy"\npassword = "dummy"\nuser_agent = "dummy"\n')

import streamlit as st
from playwright.sync_api import sync_playwright

# --- IMPORT AN TOÀN ---
try:
    from threads_scraper import get_threads_content
    from video_creation.background import (
        chop_background, download_background_audio, 
        download_background_video, get_background_config
    )
    from video_creation.final_video import make_final_video
    from video_creation.voices import save_text_to_mp3
except Exception:
    pass

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
        # Cài trình duyệt trước khi launch để chắc ăn
        install_playwright_browsers()
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(device_scale_factor=2)
        html_content = f"""
        <div style="background:#000; color:white; padding:50px; border-radius:30px; font-family:sans-serif; font-size:40px; border:2px solid #333; text-align:center;">
            <p style="color:#1d9bf0; font-weight:bold;">@Threads_Trending_Bot</p>
            <div style="margin-top:20px; line-height:1.4;">{text}</div>
        </div>
        """
        page.set_content(html_content)
        page.locator("div").first.screenshot(path="assets/temp/png/title.png", omit_background=True)
        browser.close()

def run_process(url):
    with st.status("🎬 Đang tạo video... Quang đợi tí nhé!", expanded=True) as status:
        # BƯỚC QUAN TRỌNG: Cài đặt Chromium trước khi cào dữ liệu
        st.write("🛠️ Đang kiểm tra trình duyệt ảo...")
        install_playwright_browsers()
        
        st.write("📡 Đang cào dữ liệu Threads...")
        text = get_threads_content(url)
        if not text:
            st.error("Không lấy được nội dung! Quang check lại link nhé.")
            return

        reddit_id = "threads_" + str(int(time.time()))
        reddit_obj = {"thread_id": reddit_id, "thread_title": text, "thread_post": "", "comments": []}

        st.write("🎙️ Đang tạo giọng đọc AI...")
        length, _ = save_text_to_mp3(reddit_obj)
        
        st.write("📸 Đang dựng ảnh bài viết...")
        tao_anh_giao_dien_threads_gia(text)

        st.write("🎞️ Đang xử lý video nền...")
        bg_config = {"video": get_background_config("video"), "audio": get_background_config("audio")}
        download_background_video(bg_config["video"])
        download_background_audio(bg_config["audio"])
        chop_background(bg_config, math.ceil(length), reddit_obj)

        st.write("🚀 Đang Render video cuối cùng...")
        make_final_video(0, math.ceil(length), reddit_obj, bg_config)
        
        status.update(label="✅ Xong rồi Quang ơi!", state="complete")
        
        video_files = sorted(Path("video_output").glob("*.mp4"), key=os.path.getmtime)
        if video_files:
            st.video(str(video_files[-1]))

# --- GIAO DIỆN ---
st.set_page_config(page_title="Threads Bot - Quang ICTU")
st.title("🧵 Threads Video Maker")
st.markdown(f"```\n{BANNER}\n```")
st.subheader("Dự án của Quang - ICTU")

link = st.text_input("🔗 Dán link Threads vào đây:")
if st.button("Bắt đầu làm Video"):
    if link.strip():
        run_process(link.strip())
    else:
        st.warning("Quang chưa nhập link kìa!")