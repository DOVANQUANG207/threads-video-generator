#!/usr/bin/env python
import os
import sys
import subprocess
import time
import math
import shutil
from pathlib import Path

# --- 1. TỰ ĐỘNG CÀI TRÌNH DUYỆT ---
def install_playwright_browsers():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception: pass

if not os.path.exists("config.toml"):
    with open("config.toml", "w", encoding="utf-8") as f:
        f.write('[reddit]\nclient_id = "dummy"\nclient_secret = "dummy"\nusername = "dummy"\npassword = "dummy"\nuser_agent = "dummy"\n')

import streamlit as st
from playwright.sync_api import sync_playwright

# --- IMPORT VÀ BẺ KHOÁ HỆ THỐNG ---
try:
    import video_creation.background as vcb
    from threads_scraper import get_threads_content
    from video_creation.final_video import make_final_video
    from video_creation.voices import save_text_to_mp3

    # PHÁP THUẬT: Ghi đè hàm bị lỗi của Bot để nó không bao giờ crash nữa
    def fixed_chop(bg_config, duration, reddit_obj):
        st.write("🪄 Pháp sư Quang đang 'bẻ khóa' video nền...")
        target = Path("assets/temp/background_video.mp4")
        target.parent.mkdir(parents=True, exist_ok=True)
        # Ép nó lấy đúng file mp4 bạn đã up lên
        source = bg_config["video"][0]
        shutil.copy(source, target)
        st.write("✅ Đã cưỡng chế video nền thành công!")

    def fake_download(config): return None

    # Áp dụng bùa chú vào hệ thống
    vcb.chop_background = fixed_chop
    vcb.download_background_video = fake_download
except Exception: pass

BANNER = "QUANG - ICTU - THREADS BOT"

def tao_anh_threads(text):
    os.makedirs("assets/temp/png", exist_ok=True)
    with sync_playwright() as p:
        install_playwright_browsers()
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(device_scale_factor=2)
        html = f'<div style="background:#000;color:white;padding:50px;font-size:40px;text-align:center;">{text}</div>'
        page.set_content(html)
        page.locator("div").first.screenshot(path="assets/temp/png/title.png")
        browser.close()

def run_process(url):
    with st.status("🚀 Đang 'nổ hũ' video... Lần này chắc chắn được!", expanded=True) as status:
        install_playwright_browsers()
        text = get_threads_content(url)
        if not text: return
        
        reddit_obj = {"thread_id": str(int(time.time())), "thread_title": text, "thread_post": "", "comments": []}
        length, _ = save_text_to_mp3(reddit_obj)
        tao_anh_threads(text)

        # Chuẩn bị nguyên liệu cho hàm "Fixed_Chop" ở trên
        video_files = list(Path("assets/backgrounds/video").glob("*.mp4"))
        if not video_files:
            st.error("Quang ơi, bạn chưa up file .mp4 nào lên GitHub kìa!")
            return
            
        bg_config = {
            "video": [str(video_files[0]), "dummy", "dummy", "dummy"], # Tạo list đủ dài để không lỗi index
            "audio": vcb.get_background_config("audio")
        }

        vcb.download_background_audio(bg_config["audio"])
        vcb.chop_background(bg_config, math.ceil(length), reddit_obj) # Gọi hàm đã được bẻ khóa

        st.write("🎬 Đang render những mét phim cuối cùng...")
        make_final_video(0, math.ceil(length), reddit_obj, bg_config)
        
        status.update(label="🎉 CHIẾN THẮNG RỒI QUANG ƠI!", state="complete")
        
        out_dir = Path("video_output")
        if out_dir.exists():
            vids = sorted(out_dir.glob("*.mp4"), key=os.path.getmtime)
            if vids: st.video(str(vids[-1]))

# --- UI ---
st.title("🧵 Threads Maker - Fix 100%")
link = st.text_input("🔗 Dán link Threads:")
if st.button("LÀM VIDEO NGAY"):
    if link: run_process(link)
