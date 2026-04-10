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

print(
    """
██████╗ ██╗   ██╗ █████╗ ███╗   ██╗ ██████╗ 
██╔═══██╗██║   ██║██╔══██╗████╗  ██║██╔════╝ 
██║   ██║██║   ██║███████║██╔██╗ ██║██║  ███╗
██║██╗██║██║   ██║██╔══██║██║╚██╗██║██║   ██║
╚██████╔╝╚██████╔╝██║  ██║██║ ╚████║╚██████╔╝
 ╚═██╔═╝  ╚═════╝  ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ 
    """
)
print_markdown("### Dự án Bot Video Threads - Quang ICTU Custom Edition")

def tao_anh_giao_dien_threads_gia(text):
    """Sử dụng Playwright để tạo ảnh giao diện Threads ảo thay cho screenshot Reddit"""
    print_step("📸 Đang tạo ảnh giao diện Threads ảo...")
    
    html_content = f"""
    <html style="background: transparent;">
    <body style="background: transparent; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
        <div style="background-color: rgba(10, 10, 10, 0.95); color: white; padding: 60px; border-radius: 40px; font-size: 48px; max-width: 1000px; text-align: center; border: 1px solid #333; box-shadow: 0 15px 50px rgba(0,0,0,0.8);">
            <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 30px;">
                <div style="width: 80px; height: 80px; background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); border-radius: 50%; margin-right: 20px;"></div>
                <p style="color: #fff; font-weight: 800; margin: 0; font-size: 40px;">threads_vn_trending</p>
            </div>
            <p style="line-height: 1.4; letter-spacing: -0.5px;">{text}</p>
        </div>
    </body>
    </html>
    """
    
    os.makedirs("assets/temp/png", exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(device_scale_factor=2)
        page.set_content(html_content)
        # Chụp ảnh và lưu đúng đường dẫn bot cũ cần
        page.locator("div").first.screenshot(path="assets/temp/png/title.png", omit_background=True)
        browser.close()
    print_substep("✅ Đã tạo xong ảnh title.png", style="bold green")

def main(threads_url) -> None:
    global reddit_id, reddit_object
    
    # 1. Cào dữ liệu
    threads_text = get_threads_content(threads_url)
    if not threads_text:
        print_step("❌ Lỗi: Không lấy được nội dung từ Threads!")
        return

    # 2. Tạo ID và Object giả lập (Mocking)
    reddit_id = "threads_" + str(int(time.time()))
    reddit_object = {
        "thread_id": reddit_id,
        "thread_title": threads_text,
        "thread_post": "",
        "comments": [] 
    }

    # 3. Tạo giọng đọc MP3
    length, number_of_comments = save_text_to_mp3(reddit_object)
    length = math.ceil(length)

    # 4. Tạo ảnh giả lập
    tao_anh_giao_dien_threads_gia(threads_text)

    # 5. Xử lý video nền
    bg_config = {
        "video": get_background_config("video"),
        "audio": get_background_config("audio"),
    }
    download_background_video(bg_config["video"])
    download_background_audio(bg_config["audio"])
    chop_background(bg_config, length, reddit_object)

    # 6. Render Video cuối cùng
    print_step("🎬 Đang ghép video hoàn chỉnh (Final Rendering)...")
    make_final_video(0, length, reddit_object, bg_config)
    print_markdown(f"## 🎉 Xong rồi Quang ơi! Video lưu tại thư mục video_output")

def shutdown() -> NoReturn:
    if "reddit_id" in globals():
        cleanup(reddit_id)
    sys.exit()

if __name__ == "__main__":
    checkversion("3.4.0")
    ffmpeg_install()
    directory = Path().absolute()
    
    # Kiểm tra config
    config = settings.check_toml(f"{directory}/utils/.config.template.toml", f"{directory}/config.toml")
    if config is False:
        sys.exit()

    try:
        url = input("\n🔗 Nhập link bài viết Threads: ").strip()
        if url:
            main(url)
        else:
            print("Link không được để trống!")
    except KeyboardInterrupt:
        shutdown()
    except Exception as e:
        print(f"‼️ Lỗi phát sinh: {e}")
        raise e
