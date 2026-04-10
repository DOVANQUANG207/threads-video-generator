#!/usr/bin/env python
import math
import sys
import time
import os
from pathlib import Path
from typing import NoReturn
from playwright.sync_api import sync_playwright

# --- MOCK CONFIG ĐỂ LỪA BOT CŨ (PHẢI ĐỂ TRÊN CÙNG) ---
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
# Tạo sẵn thư mục output
os.makedirs("video_output", exist_ok=True)

# Module cào dữ liệu Threads của anh em mình
from threads_scraper import get_threads_content

from utils import settings
from utils.cleanup import cleanup
from utils.console import print_markdown, print_step, print_substep
# Chặn đứng hàm cài đặt FFmpeg cũ nếu chạy trên mây
from utils.ffmpeg_install import ffmpeg_install
from utils.version import checkversion
from video_creation.background import (
    chop_background,
    download_background_audio,
    download_background_video,
    get_background_config,
)
from video_creation.final_video import make_final_video
from video_creation.voices import save_text_to_mp3

__VERSION__ = "3.4.0 (Threads Edition)"

BANNER = """
██████╗ ██╗   ██╗ █████╗ ███╗   ██╗ ██████╗ 
██╔═══██╗██║   ██║██╔══██╗████╗  ██║██╔════╝ 
██║   ██║██║   ██║███████║██╔██╗ ██║██║  ███╗
██║██╗██║██║   ██║██╔══██║██║╚██╗██║██║   ██║
╚██████╔╝╚██████╔╝██║  ██║██║ ╚████║╚██████╔╝
 ╚═██╔═╝  ╚═════╝  ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ 
"""

def tao_anh_giao_dien_threads_gia(text):
    print_step("📸 Đang tạo ảnh giao diện Threads ảo...")
    html_content = f"""
    <html style="background: transparent;">
    <body style="background: transparent; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; font-family: sans-serif;">
        <div style="background-color: rgba(10, 10, 10, 0.95); color: white; padding: 60px; border-radius: 40px; font-size: 48px; max-width: 1000px; text-align: center; border: 1px solid #333;">
            <p style="color: #1d9bf0; font-weight: bold; font-size: 40px;">@Threads_Trending_Bot</p>
            <p style="line-height: 1.4;">{text}</p>
        </div>
    </body>
    </html>
    """
    os.makedirs("assets/temp/png", exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(device_scale_factor=2)
        page.set_content(html_content)
        page.locator("div").first.screenshot(path="assets/temp/png/title.png", omit_background=True)
        browser.close()

def main(threads_url) -> None:
    global reddit_id, reddit_object
    is_streamlit = "STREAMLIT_SERVER_PORT" in os.environ
    
    if is_streamlit:
        import streamlit as st
        status = st.status("🎬 Đang xử lý video... Quang đợi tí nhé!")
    else: status = None

    try:
        threads_text = get_threads_content(threads_url)
        if not threads_text:
            if is_streamlit: st.error("❌ Không lấy được nội dung Threads!")
            return

        reddit_id = "threads_" + str(int(time.time()))
        reddit_object = {"thread_id": reddit_id, "thread_title": threads_text, "thread_post": "", "comments": []}

        if is_streamlit: st.write("🎙️ Đang tạo giọng đọc AI...")
        length, _ = save_text_to_mp3(reddit_object)
        length = math.ceil(length)
        
        tao_anh_giao_dien_threads_gia(threads_text)

        if is_streamlit: st.write("🎥 Chuẩn bị video nền...")
        bg_config = {"video": get_background_config("video"), "audio": get_background_config("audio")}
        download_background_video(bg_config["video"])
        download_background_audio(bg_config["audio"])
        chop_background(bg_config, length, reddit_object)

        if is_streamlit: st.write("⚙️ Đang Render video...")
        make_final_video(0, length, reddit_object, bg_config)
        
        if is_streamlit:
            status.update(label="🎉 Thành công rồi Quang ơi!", state="complete")
            video_files = sorted(Path("video_output").glob("*.mp4"), key=os.path.getmtime)
            if video_files: st.video(str(video_files[-1]))
        
        print_markdown(f"## 🎉 Xong rồi Quang ơi!")
    except Exception as e:
        if is_streamlit: st.error(f"‼️ Lỗi: {e}")

def shutdown() -> NoReturn:
    if "reddit_id" in globals(): cleanup(reddit_id)
    sys.exit()

if __name__ == "__main__":
    is_streamlit = "STREAMLIT_SERVER_PORT" in os.environ
    
    if is_streamlit:
        import streamlit as st
        st.set_page_config(page_title="Threads Video Maker - Quang ICTU")
        st.title("🧵 Threads Video Maker - By Quang")
        st.markdown(f"```\n{BANNER}\n```")
        
        # --- BƯỚC QUAN TRỌNG: CÀI FFMEG VÀ FIX CONFIG ---
        # Trên Streamlit mình đã có packages.txt nên không gọi ffmpeg_install()
        # Mình giả lập config để nó không hỏi Reddit nữa
        if not os.path.exists("config.toml"):
            with open("config.toml", "w") as f:
                f.write('[reddit]\nclient_id = "dummy"\nclient_secret = "dummy"\nusername = "dummy"\npassword = "dummy"\nuser_agent = "dummy"')

        url = st.text_input("🔗 Nhập link bài viết Threads vào đây:")
        if st.button("Làm Video ngay!"):
            if url.strip(): main(url.strip())
            else: st.warning("Quang chưa nhập link kìa!")
    else:
        print(BANNER)
        ffmpeg_install()
        url = input("\n🔗 Nhập link bài viết Threads: ").strip()
        if url: main(url)
