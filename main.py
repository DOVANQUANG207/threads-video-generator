#!/usr/bin/env python
import os
import sys

# --- BƯỚC 1: GIẢ LẬP CONFIG NGAY LẬP TỨC ---
# Điều này chặn đứng việc Bot hỏi "Reddit ID là gì" ở Terminal
if not os.path.exists("config.toml"):
    with open("config.toml", "w", encoding="utf-8") as f:
        f.write('[reddit]\nclient_id = "dummy"\nclient_secret = "dummy"\nusername = "dummy"\npassword = "dummy"\nuser_agent = "dummy"\n')

import math
import time
import streamlit as st
from pathlib import Path
from typing import NoReturn
from playwright.sync_api import sync_playwright

# --- BANNER CỦA QUANG ---
BANNER = """
██████╗ ██╗   ██╗ █████╗ ███╗   ██╗ ██████╗ 
██╔═══██╗██║   ██║██╔══██╗████╗  ██║██╔════╝ 
██║   ██║██║   ██║███████║██╔██╗ ██║██║  ███╗
██║██╗██║██║   ██║██╔══██║██║╚██╗██║██║   ██║
╚██████╔╝╚██████╔╝██║  ██║██║ ╚████║╚██████╔╝
 ╚═██╔═╝  ╚═════╝  ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ 
"""

# Import các module sau khi đã có config giả
try:
    from threads_scraper import get_threads_content
    from utils import settings
    from utils.cleanup import cleanup
    from utils.console import print_markdown, print_step, print_substep
    from utils.ffmpeg_install import ffmpeg_install
    from video_creation.background import (
        chop_background, download_background_audio, 
        download_background_video, get_background_config
    )
    from video_creation.final_video import make_final_video
    from video_creation.voices import save_text_to_mp3
except Exception as e:
    st.error(f"⚠️ Đang khởi tạo thư viện: {e}")

def tao_anh_giao_dien_threads_gia(text):
    os.makedirs("assets/temp/png", exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(device_scale_factor=2)
        html_content = f"""
        <div style="background:#000; color:white; padding:50px; border-radius:30px; font-family:sans-serif; font-size:40px; border:1px solid #333;">
            <p style="color:#1d9bf0; font-weight:bold;">@Threads_Trending_Bot</p>
            <div style="margin-top:20px;">{text}</div>
        </div>
        """
        page.set_content(html_content)
        page.locator("div").first.screenshot(path="assets/temp/png/title.png", omit_background=True)
        browser.close()

def run_process(url):
    with st.status("🎬 Đang tạo video... Quang đợi tí nhé!") as status:
        st.write("📡 Đang cào dữ liệu Threads...")
        text = get_threads_content(url)
        if not text:
            st.error("Không lấy được nội dung!")
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

# --- GIAO DIỆN CHÍNH ---
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

if __name__ == "__main__":
    if "STREAMLIT_SERVER_PORT" not in os.environ:
        # Chạy ở máy local
        ffmpeg_install()
