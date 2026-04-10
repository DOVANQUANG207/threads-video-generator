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
    try:
        (
            ffmpeg.input(f"assets/temp/{reddit_id}/background.mp4")
            .filter("crop", f"ih*({W}/{H})", "ih")
            # Thêm pix_fmt="yuv420p" cực kỳ quan trọng để Streamlit không bị sập
            .output(output_path, an=None, vcodec="libx264", crf=23, preset="veryfast", pix_fmt="yuv420p")
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True) # Bắt lỗi rõ ràng
        )
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf8', errors='ignore') if e.stderr else str(e)
        print(f"⚠️ Lỗi Crop Video: {error_msg}")
        # Nếu crop lỗi, trả về luôn video gốc để cứu vãn
        return f"assets/temp/{reddit_id}/background.mp4"
    return output_path

def create_fancy_thumbnail(image, text, text_color, padding, wrap=35):
    try:
        font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), 47)
        draw = ImageDraw.Draw(image)
    except:
        pass
    return image

def make_final_video(number_of_clips, length, reddit_obj, background_config):
    from utils import settings
    
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
        st.error(f"❌ Video nền không hợp lệ hoặc trống. Quang kiểm tra lại khâu Upload nhé!")
        return

    # Render bằng ffmpeg với CPU (libx264)
    background_no_audio = prepare_background(reddit_id, W, H)
    
    # Tìm file audio (phòng trường hợp nó lưu khác tên)
    audio_path = ""
    possible_audios = [f"assets/temp/{reddit_id}/audio.mp3", f"assets/temp/{reddit_id}/{reddit_id}.mp3"]
    for pa in possible_audios:
        if os.path.exists(pa) and os.path.getsize(pa) > 0:
            audio_path = pa
            break
            
    output_dir = "video_output"
    os.makedirs(output_dir, exist_ok=True)
    final_path = f"{output_dir}/video_cua_quang.mp4"

    try:
        input_video = ffmpeg.input(background_no_audio)
        
        # Nếu TÌM THẤY âm thanh, ghép cả hình lẫn tiếng
        if audio_path:
            input_audio = ffmpeg.input(audio_path)
            (
                ffmpeg.output(input_video, input_audio, final_path, vcodec="libx264", acodec="aac", strict="experimental", pix_fmt="yuv420p", shortest=None)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
        # Nếu KHÔNG CÓ âm thanh, chỉ render hình để tránh lỗi sập App
        else:
            print("⚠️ Không tìm thấy file âm thanh, tiến hành render video không tiếng.")
            (
                ffmpeg.output(input_video, final_path, vcodec="libx264", strict="experimental", pix_fmt="yuv420p")
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
        st.success("🔥 Render xong! Quang xem video bên dưới nhé.")
        
    except ffmpeg.Error as e:
        error_details = e.stderr.decode('utf8', errors='ignore') if e.stderr else str(e)
        st.error(f"❌ Lỗi Render cuối cùng! Cỗ máy FFmpeg báo: {error_details}")