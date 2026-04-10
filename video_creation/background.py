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
        video_path = "./utils/background_videos.json"
        if os.path.exists(video_path):
            with open(video_path) as json_file:
                _background_options["video"] = json.load(json_file)
        audio_path = "./utils/background_audios.json"
        if os.path.exists(audio_path):
            with open(audio_path) as json_file:
                _background_options["audio"] = json.load(json_file)
    except: pass
    return _background_options

def get_start_and_end_times(video_length: int, length_of_clip: int) -> Tuple[int, int]:
    if int(length_of_clip) <= int(video_length): return 0, int(length_of_clip)
    max_start = max(0, int(length_of_clip) - int(video_length) - 5)
    random_time = randrange(0, max_start) if max_start > 0 else 0
    return random_time, random_time + video_length

def get_background_config(mode: str):
    return ("https://www.youtube.com/watch?v=n_Dv46ThnEw", "video.mp4", "custom", "center")

def download_background_video(config): pass
def download_background_audio(config): pass

def chop_background(background_config: Dict[str, Any], video_length: int, reddit_object: dict):
    thread_id = re.sub(r"[^\w\s-]", "", reddit_object["thread_id"])
    temp_path = f"assets/temp/{thread_id}"
    os.makedirs(temp_path, exist_ok=True)

    # 1. XỬ LÝ NHẠC NỀN
    print_step("✂️ Cắt nhạc...")
    audio_dir = Path("assets/backgrounds/audio")
    audios = list(audio_dir.glob("*.mp3")) + list(audio_dir.glob("*.m4a"))
    if audios:
        with AudioFileClip(str(audios[0])) as background_audio:
            start, end = get_start_and_end_times(video_length, background_audio.duration)
            background_audio.subclipped(start, end).write_audiofile(f"{temp_path}/background.mp3", logger=None)

    # 2. XỬ LÝ VIDEO NỀN - FIX TRIỆT ĐỂ CHO QUANG ICTU
    print_step("✂️ Cắt video...")
    video_dir = Path("assets/backgrounds/video")
    vids = list(video_dir.glob("*.mp4"))
    
    if not vids:
        st.error("❌ Quang ơi, không tìm thấy file .mp4 nào trong assets/backgrounds/video!")
        return False

    video_full_path = str(vids[0])
    print_substep(f"✅ Đã chọn video: {video_full_path}")

    with VideoFileClip(video_full_path) as video:
        start, end = get_start_and_end_times(video_length, video.duration)
        new_video = video.subclipped(start, end)
        new_video.write_videofile(f"{temp_path}/background.mp4", codec="libx264", audio=False, logger=None)
    
    return True

background_options = load_background_options()