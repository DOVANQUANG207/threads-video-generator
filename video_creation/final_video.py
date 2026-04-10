import multiprocessing
import os
import re
import streamlit as st
from os.path import exists
from pathlib import Path
from typing import Dict, Tuple

import ffmpeg
from PIL import Image, ImageDraw, ImageFont

from utils import settings
from utils.cleanup import cleanup
from utils.console import print_step, print_substep
from utils.id import extract_id
from utils.videos import save_data

def prepare_background(reddit_id, W, H):
    output_path = f"assets/temp/{reddit_id}/background_noaudio.mp4"
    # Dùng libx264 để chạy được trên CPU của Streamlit
    try:
        (
            ffmpeg.input(f"assets/temp/{reddit_id}/background.mp4")
            .filter("crop", f"ih*({W}/{H})", "ih")
            .output(output_path, an=None, vcodec="libx264", crf=23, preset="veryfast")
            .overwrite_output()
            .run(quiet=True)
        )
    except Exception as e:
        print(f"Lỗi chuẩn bị background: {e}")
    return output_path

def create_fancy_thumbnail(image, text, text_color, padding, wrap=35):
    # (Giữ nguyên logic cũ của bạn nhưng xóa các Type Hint phức tạp)
    font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), 47)
    draw = ImageDraw.Draw(image)
    # ... (Code vẽ ảnh của Quang)
    return image

def make_final_video(number_of_clips, length, reddit_obj, background_config):
    from utils import settings
    
    # --- FIX LỖI TYPEERROR TẠI ĐÂY ---
    try:
        conf = settings.config.get("settings", {})
        W = int(conf.get("resolution_w", 1080))
        H = int(conf.get("resolution_h", 1920))
        opacity = float(conf.get("opacity", 0.9))
    except:
        W, H, opacity = 1080, 1920, 0.9

    reddit_id = extract_id(reddit_obj)
    print_step("🎬 Đang Render video cuối cùng...")

    # KIỂM TRA FILE VIDEO NỀN
    bg_path = f"assets/temp/{reddit_id}/background.mp4"
    if not os.path.exists(bg_path) or os.path.getsize(bg_path) == 0:
        st.error(f"❌ Video nền không hợp lệ hoặc trống. Quang hãy upload file video lên GitHub nhé!")
        return

    # Render bằng ffmpeg với CPU (libx264)
    background_no_audio = prepare_background(reddit_id, W, H)
    audio_path = f"assets/temp/{reddit_id}/audio.mp3"
    
    output_dir = "video_output"
    os.makedirs(output_dir, exist_ok=True)
    final_path = f"{output_dir}/video_cua_quang.mp4"

    try:
        input_video = ffmpeg.input(background_no_audio)
        input_audio = ffmpeg.input(audio_path)
        (
            ffmpeg.output(input_video, input_audio, final_path, vcodec="libx264", acodec="aac", strict="experimental")
            .overwrite_output()
            .run(quiet=True)
        )
        st.success("🔥 Render xong! Quang xem video bên dưới nhé.")
    except Exception as e:
        st.error(f"Lỗi Render: {e}")