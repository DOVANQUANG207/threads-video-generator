#!/usr/bin/env python
import math
import sys
import time
import os
from os import name
from pathlib import Path
from subprocess import Popen
from typing import Dict, NoReturn
from playwright.sync_api import sync_playwright # Thêm cái này để vẽ ảnh

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

print_markdown("### Chào mừng Quang đến với VideoMakerBot - Phiên bản độ lại cho Threads!")

def tao_anh_giao_dien_threads_gia(text):
    """Hàm này dùng Playwright vẽ ra một cái ảnh chứa chữ để lừa máy ghép video"""
    print_step("📸 Đang tạo ảnh giao diện Threads ảo...")
    
    # HTML này tạo ra một cái bảng màu đen, chữ trắng, bo góc nhìn y hệt Threads
    html_content = f"""
    <html style="background: transparent;">
    <body style="background: transparent; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; font-family: sans-serif;">
        <div style="background-color: rgba(15, 15, 15, 0.9); color: white; padding: 50px; border-radius: 30px; font-size: 45px; max-width: 900px; text-align: center; border: 2px solid #333; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
            <p style="color: #00BFFF; font-weight: bold; margin-bottom: 20px; font-size: 35px;">@User_Threads</p>
            {text}
        </div>
    </body>
    </html>
    """
    
    # Bot cũ thường tìm ảnh ở thư mục này, mình tạo sẵn cho nó
    os.makedirs("assets/temp/png", exist_ok=True)
    
    # Mở trình duyệt ẩn lên, dán HTML vào và chụp ảnh cái Cạch!
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(device_scale_factor=2) # Chụp độ phân giải cao cho nét
        page.set_content(html_content)
        # Lưu đè đúng tên file ảnh mà code cũ hay dùng (thường là title.png)
        page.locator("div").screenshot(path="assets/temp/png/title.png", omit_background=True)
        browser.close()
    print_substep("✅ Đã rửa ảnh xong!", style="bold green")

def main(threads_url) -> None:
    global reddit_id, reddit_object
    print_substep(f"🚀 Đang cào link: {threads_url}", style="bold blue")
    
    # 1. Cào text
    threads_text = get_threads_content(threads_url)
    if not threads_text:
        return

    # 2. Tạo Data Giả
    reddit_id = "threads_" + str(int(time.time()))
    reddit_object = {
        "thread_id": reddit_id,
        "thread_title": threads_text,
        "thread_post": "",
        "comments": [] 
    }

    # 3. Tạo Giọng nói
    length, number_of_comments = save_text_to_mp3(reddit_object)
    length = math.ceil(length)

    # 4. TẠO ẢNH GIẢ (Thay thế hàm get_screenshots_of_reddit_posts cũ)
    tao_anh_giao_dien_threads_gia(threads_text)

    # 5. Làm video nền
    bg_config = {
        "video": get_background_config("video"),
        "audio": get_background_config("audio"),
    }
    download_background_video(bg_config["video"])
    download_background_audio(bg_config["audio"])
    chop_background(bg_config, length, reddit_object)

    # 6. Lắp ráp Video
    print_step("⚠️ Đang Render Video hoàn chỉnh...")
    # Vì mình không có comments, truyền số 0 vào để nó chỉ ghép mỗi cái title.png
    make_final_video(0, length, reddit_object, bg_config)
    print_markdown("## 🎉 THÀNH CÔNG! VIDEO ĐÃ RA LÒ!")


def shutdown() -> NoReturn:
    if "reddit_id" in globals():
        cleanup(reddit_id)
    sys.exit()

if __name__ == "__main__":
    ffmpeg_install()
    directory = Path().absolute()
    config = settings.check_toml(f"{directory}/utils/.config.template.toml", f"{directory}/config.toml")
    config is False and sys.exit()

    try:
        link = input("\n👉 Nhập link bài viết Threads: ")
        if link.strip():
            main(link)
        else:
            print("Bạn chưa nhập link!")
    except KeyboardInterrupt:
        shutdown()
