import json
import random
import re
import os
import streamlit as st
from pathlib import Path
from random import randrange
from typing import Any, Dict, Tuple

import yt_dlp
from moviepy import AudioFileClip, VideoFileClip

from utils import settings
from utils.console import print_step, print_substep

def load_background_options():
    _background_options = {"video": {}, "audio": {}}
    try:
        # Tải danh sách video nền
        video_path = "./utils/background_videos.json"
        if os.path.exists(video_path):
            with open(video_path) as json_file:
                _background_options["video"] = json.load(json_file)
        
        # Tải danh sách nhạc nền
        audio_path = "./utils/background_audios.json"
        if os.path.exists(audio_path):
            with open(audio_path) as json_file:
                _background_options["audio"] = json.load(json_file)

        # Xử lý các ghi chú trong file JSON
        if "__comment" in _background_options["video"]: del _background_options["video"]["__comment"]
        if "__comment" in _background_options["audio"]: del _background_options["audio"]["__comment"]

        for name in list(_background_options["video"].keys()):
            if len(_background_options["video"][name]) > 3:
                pos = _background_options["video"][name][3]
                if pos != "center":
                    _background_options["video"][name][3] = lambda t: ("center", pos + t)
    except Exception as e:
        print(f"⚠️ Cảnh báo: Không load được file JSON background: {e}")
    
    return _background_options

def get_start_and_end_times(video_length: int, length_of_clip: int) -> Tuple[int, int]:
    if int(length_of_clip) <= int(video_length):
        return 0, int(length_of_clip)
    
    max_start = max(0, int(length_of_clip) - int(video_length) - 5)
    random_time = randrange(0, max_start) if max_start > 0 else 0
    return random_time, random_time + video_length

def get_background_config(mode: str):
    """Lấy cấu hình background an toàn và hỗ trợ vượt lỗi 403."""
    try:
        config_section = settings.config.get("settings", {}).get("background", {})
        choice = str(config_section.get(f"background_{mode}", "")).casefold()
    except Exception:
        choice = None

    options = background_options.get(mode, {})
    if not choice or choice not in options:
        if options:
            choice = random.choice(list(options.keys()))
        else:
            # Fallback nếu không có dữ liệu JSON
            return ("https://www.youtube.com/watch?v=n_Dv46ThnEw", "minecraft.mp4", "mc_cre", "center")

    return options[choice]

def download_background_video(background_config: Tuple[str, str, str, Any]):
    Path("./assets/backgrounds/video/").mkdir(parents=True, exist_ok=True)
    uri, filename, credit, _ = background_config
    save_path = f"assets/backgrounds/video/{credit}-{filename}"
    if Path(save_path).is_file(): return
    
    print_step(f"📥 Đang chuẩn bị tải video nền: {filename}")
    
    ydl_opts = {
        "format": "bestvideo[height<=720][ext=mp4]", 
        "outtmpl": save_path,
        "retries": 5,
        "nocheckcertificate": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    # --- CẤU HÌNH COOKIE FILE ĐỂ VƯỢT RÀO ---
    if os.path.exists("cookies.txt"):
        ydl_opts["cookiefile"] = "cookies.txt"
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([uri])
    except Exception as e:
        st.warning("⚠️ YouTube chặn tải (403). Đang sử dụng phương thức dự phòng hoặc yêu cầu upload thủ công.")
        if not os.path.exists(save_path):
            Path(save_path).touch()

def download_background_audio(background_config: Tuple[str, str, str]):
    Path("./assets/backgrounds/audio/").mkdir(parents=True, exist_ok=True)
    uri, filename, credit = background_config
    save_path = f"assets/backgrounds/audio/{credit}-{filename}"
    if Path(save_path).is_file(): return
    
    print_step(f"📥 Đang chuẩn bị tải nhạc nền: {filename}")
    ydl_opts = {
        "outtmpl": save_path,
        "format": "bestaudio/best",
        "nocheckcertificate": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    if os.path.exists("cookies.txt"):
        ydl_opts["cookiefile"] = "cookies.txt"
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([uri])
    except Exception as e:
        print(f"⚠️ Lỗi tải audio: {e}")
        if not os.path.exists(save_path):
            Path(save_path).touch()

def chop_background(background_config: Dict[str, Tuple], video_length: int, reddit_object: dict):
    thread_id = re.sub(r"[^\w\s-]", "", reddit_object["thread_id"])
    temp_path = f"assets/temp/{thread_id}"
    os.makedirs(temp_path, exist_ok=True)

    try:
        volume = settings.config.get("settings", {}).get("background", {}).get("background_audio_volume", 0.15)
    except:
        volume = 0.15

    if volume > 0:
        print_step("✂️ Đang xử lý nhạc nền...")
        audio_choice = f"{background_config['audio'][2]}-{background_config['audio'][1]}"
        audio_full_path = f"assets/backgrounds/audio/{audio_choice}"
        if os.path.exists(audio_full_path) and os.path.getsize(audio_full_path) > 0:
            with AudioFileClip(audio_full_path) as background_audio:
                start, end = get_start_and_end_times(video_length, background_audio.duration)
                background_audio.subclipped(start, end).write_audiofile(f"{temp_path}/background.mp3", logger=None)

    print_step("✂️ Đang xử lý video nền...")
    video_choice = f"{background_config['video'][2]}-{background_config['video'][1]}"
    video_full_path = f"assets/backgrounds/video/{video_choice}"
    
    if os.path.exists(video_full_path) and os.path.getsize(video_full_path) > 0:
        with VideoFileClip(video_full_path) as video:
            start, end = get_start_and_end_times(video_length, video.duration)
            new_video = video.subclipped(start, end)
            new_video.write_videofile(f"{temp_path}/background.mp4", codec="libx264", audio=False, logger=None)
    
    return background_config["video"][2]

# Khởi tạo danh sách lựa chọn
background_options = load_background_options()