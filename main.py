#!/usr/bin/env python
import os
import sys
import subprocess
import time
import math
import random
from pathlib import Path

# --- 1. TỰ ĐỘNG CÀI TRÌNH DUYỆT ---
def install_playwright_browsers():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception:
        pass

# Giả lập config
if not os.path.exists("config.toml"):
    with open("config.toml", "w", encoding="utf-8") as f:
        f.write('[reddit]\nclient_id = "dummy"\nclient_secret = "dummy"\nusername = "dummy"\npassword = "dummy"\nuser_agent = "dummy"\n')

import streamlit as st
from playwright.sync_api import sync_playwright

# --- IMPORT CÁC THƯ VIỆN CỦA BOT ---
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
    with st.status("🎬 Đang xử lý... Sắp được nghỉ rồi Quang ơi!", expanded=True) as status:
        st.write("🛠️ Kiểm tra trình duyệt...")
        install_playwright_browsers()
        
        st.write("📡 Lấy bài đăng Threads...")
        text = get_threads_content(url)
        if not text:
            st.error("Không lấy được nội dung!")
            return

        reddit_id = "threads_" + str(int(time.time()))
        reddit_obj = {"thread_id": reddit_id, "thread_title": text, "thread_post": "", "comments": []}

        st.write("🎙️ Tạo giọng AI...")
        length, _ = save_text_to_mp3(reddit_obj)
        
        st.write("📸 Dựng ảnh giao diện...")
        tao_anh_giao_dien_threads_gia(text)

        st.write("🎞️ Xử lý video nền (Bản fix 1000%)...")
        video_folder = Path("assets/backgrounds/video")
        video_files = list(video_folder.glob("*.mp4"))
        
        if video_files:
            # Lấy cái tên file (ví dụ: parkour.mp4)
            selected_video_name = video_files[0].name
            # BỎ CÁI ĐUÔI .mp4 để Bot nó tự ghép lại
            clean_name = selected_video_name.replace(".mp4", "")
            
            st.write(f"✅ Đã chọn file: {selected_video_name}")
            
            # TẠO DANH SÁCH GIẢ ĐÚNG Ý BOT (Index 2 là cái tên file)
            bg_config = {
                "video": ["Quang_ICTU", "Video_Nen", clean_name, "0", "0"], 
                "audio": get_background_config("audio")
            }
        else:
            st.error("⚠️ Không tìm thấy file video nào trong assets/backgrounds/video!")
            return

        st.write("✂️ Đang cắt video và nhạc...")
        # Ép nó không tải video nữa
        download_background_audio(bg_config["audio"])
        chop_background(bg_config, math.ceil(length), reddit_obj)

        st.write("🚀 Đang Render video cuối cùng...")
        make_final_video(0, math.ceil(length), reddit_obj, bg_config)
        
        status.update(label="🔥 THÀNH CÔNG RỰC RỠ!", state="complete")
        
        video_output_dir = Path("video_output")
        if video_output_dir.exists():
            final_videos = sorted(video_output_dir.glob("*.mp4"), key=os.path.getmtime)
            if final_videos:
                st.success("Video của Quang xong rồi nè! 👇")
                st.video(str(final_videos[-1]))

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
        st.warning("Quang nhập link đi đã!")
