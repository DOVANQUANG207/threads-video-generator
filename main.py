#!/usr/bin/env python
import math
import sys
import time
import os
from os import name
from pathlib import Path
from subprocess import Popen
from typing import Dict, NoReturn
from playwright.sync_api import sync_playwright

# Module cào dữ liệu Threads của anh em mình
from threads_scraper import get_threads_content

from utils import settings
from utils.cleanup import cleanup
from utils.console import print_markdown, print_step, print_substep
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

# --- BANNER CỦA QUANG ---
BANNER = """
██████╗ ██╗   ██╗ █████╗ ███╗   ██╗ ██████╗ 
██╔═══██╗██║   ██║██╔══██╗████╗  ██║██╔════╝ 
██║   ██║██║   ██║███████║██╔██╗ ██║██║  ███╗
██║██╗██║██║   ██║██╔══██║██║╚██╗██║██║   ██║
╚██████╔╝╚██████╔╝██║  ██║██║ ╚████║╚██████╔╝
 ╚═██╔═╝  ╚═════╝  ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ 
"""

def tao_anh_giao_dien_threads_gia(text):
    """Tạo ảnh Threads ảo lừa máy Render"""
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
    print_substep(f"🚀 Bắt đầu xử lý link: {threads_url}", style="bold blue")
    
    threads_text = get_threads_content(threads_url)
    if not threads_text:
        print_step("❌ Lỗi: Không lấy được nội dung!")
        return

    reddit_id = "threads_" + str(int(time.time()))
    reddit_object = {"thread_id": reddit_id, "thread_title": threads_text, "thread_post": "", "comments": []}

    length, _ = save_text_to_mp3(reddit_object)
    length = math.ceil(length)
    tao_anh_giao_dien_threads_gia(threads_text)

    bg_config = {"video": get_background_config("video"), "audio": get_background_config("audio")}
    download_background_video(bg_config["video"])
    download_background_audio(bg_config["audio"])
    chop_background(bg_config, length, reddit_object)

    print_step("🎬 Đang ghép video hoàn chỉnh...")
    make_final_video(0, length, reddit_object, bg_config)
    print_markdown(f"## 🎉 Xong rồi Quang ơi! Check video trong thư mục video_output nhé!")

def shutdown() -> NoReturn:
    if "reddit_id" in globals():
        cleanup(reddit_id)
    sys.exit()

if __name__ == "__main__":
    # Kiểm tra xem có đang chạy trên Streamlit Cloud không
    is_streamlit = "STREAMLIT_SERVER_PORT" in os.environ
    
    if not is_streamlit:
        print(BANNER)
        print_markdown("### Dự án Bot Video Threads - Quang ICTU Custom Edition")
        checkversion("3.4.0")
    else:
        import streamlit as st
        st.title("🧵 Threads Video Maker - By Quang")

    ffmpeg_install()
    directory = Path().absolute()
    config = settings.check_toml(f"{directory}/utils/.config.template.toml", f"{directory}/config.toml")
    
    try:
        if is_streamlit:
            url = st.text_input("🔗 Nhập link bài viết Threads:")
            if st.button("Làm Video ngay!"):
                if url: main(url)
        else:
            url = input("\n🔗 Nhập link bài viết Threads: ").strip()
            if url: main(url)
    except KeyboardInterrupt:
        shutdown()
