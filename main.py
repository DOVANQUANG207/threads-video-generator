#!/usr/bin/env python
import os, sys, subprocess, time, math
from pathlib import Path
import streamlit as st

# Tự động cài trình duyệt Playwright
def install_playwright():
    try: subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except: pass

# Tạo config giả để tránh lỗi thư viện
if not os.path.exists("config.toml"):
    with open("config.toml", "w") as f: f.write('[reddit]\nclient_id="d"\nclient_secret="d"\nusername="d"\npassword="d"\nuser_agent="d"\n')

from threads_scraper import get_threads_content
from video_creation.background import chop_background, get_background_config
from video_creation.final_video import make_final_video
from video_creation.voices import save_text_to_mp3

st.set_page_config(page_title="Threads Bot - Quang ICTU")
st.title("🧵 Threads Video Maker")
st.subheader("Dự án của Quang - ICTU (Bản Fix Cố Định)")

link = st.text_input("🔗 Dán link Threads vào đây:")

if st.button("LÀM VIDEO NGAY"):
    if link.strip():
        with st.status("🚀 Đang làm video... Lần này nổ hũ chắc luôn!") as status:
            # 1. Chuẩn bị hệ thống
            install_playwright()
            
            # 2. Cào dữ liệu
            text = get_threads_content(link.strip())
            if not text:
                st.error("Lỗi: Không lấy được nội dung Threads.")
                return
            
            reddit_obj = {"thread_id": str(int(time.time())), "thread_title": text, "thread_post": "", "comments": []}
            
            # 3. Tạo tiếng và ảnh
            st.write("🎙️ Đang tạo giọng AI và ảnh...")
            length, _ = save_text_to_mp3(reddit_obj)
            
            # 4. Cắt video nền (Dùng hàm đã fix)
            st.write("🎞️ Đang xử lý video nền có sẵn...")
            bg_config = {"video": get_background_config("video"), "audio": get_background_config("audio")}
            success = chop_background(bg_config, math.ceil(length), reddit_obj)
            
            if success:
                # 5. Render cuối
                st.write("🎬 Đang Render thành phẩm...")
                make_final_video(0, math.ceil(length), reddit_obj, bg_config)
                
                status.update(label="🎉 CHIẾN THẮNG RỒI QUANG ƠI!", state="complete")
                
                vids = sorted(Path("video_output").glob("*.mp4"), key=os.path.getmtime)
                if vids: st.video(str(vids[-1]))
            else:
                st.error("Dừng lại do không thấy video nền.")
    else:
        st.warning("Quang quên nhập link kìa!")