import os
import re
import streamlit as st
from pathlib import Path
import ffmpeg
from utils.id import extract_id

def prepare_background(reddit_id, W, H):
    output_path = f"assets/temp/{reddit_id}/background_noaudio.mp4"
    try:
        (
            ffmpeg.input(f"assets/temp/{reddit_id}/background.mp4")
            .filter("crop", f"ih*({W}/{H})", "ih")
            .output(output_path, an=None, vcodec="libx264", crf=23, preset="veryfast", pix_fmt="yuv420p")
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error:
        return f"assets/temp/{reddit_id}/background.mp4"
    return output_path

def make_final_video(number_of_clips, length, reddit_obj, background_config):
    try:
        from utils import settings
        conf = settings.config.get("settings", {})
        W = int(conf.get("resolution_w", 1080))
        H = int(conf.get("resolution_h", 1920))
    except:
        W, H = 1080, 1920

    reddit_id = extract_id(reddit_obj)
    
    # 1. Đảm bảo có video nền
    bg_path = f"assets/temp/{reddit_id}/background.mp4"
    if not os.path.exists(bg_path):
        st.error("❌ Mất tích video nền!")
        return

    background_no_audio = prepare_background(reddit_id, W, H)

    # 2. Tìm file ẢNH CHỮ (Cái mà Quang đang bảo thiếu đây)
    image_path = "assets/temp/png/title.png"

    # 3. Tìm file GIỌNG ĐỌC AI (Tìm mọi file mp3 trong thư mục)
    temp_dir = Path(f"assets/temp/{reddit_id}")
    audio_files = list(temp_dir.glob("*.mp3"))
    audio_path = str(audio_files[0]) if audio_files else ""

    output_dir = "video_output"
    os.makedirs(output_dir, exist_ok=True)
    final_path = f"{output_dir}/video_cua_quang.mp4"

    try:
        # Chuẩn bị nguyên liệu
        input_video = ffmpeg.input(background_no_audio)
        
        # Nếu có ảnh chữ, dán ảnh vào giữa video (scale ảnh bằng 85% chiều rộng video)
        if os.path.exists(image_path):
            input_image = ffmpeg.input(image_path)
            input_image = ffmpeg.filter(input_image, 'scale', f'trunc({W}*0.85)', '-1')
            # Lệnh overlay: Dán ảnh lên video
            input_video = ffmpeg.overlay(input_video, input_image, x="(main_w-overlay_w)/2", y="(main_h-overlay_h)/2")

        # Ghép âm thanh AI
        if audio_path:
            input_audio = ffmpeg.input(audio_path)
            (
                ffmpeg.output(input_video, input_audio, final_path, vcodec="libx264", acodec="aac", strict="experimental", pix_fmt="yuv420p", shortest=None)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
        else:
            (
                ffmpeg.output(input_video, final_path, vcodec="libx264", strict="experimental", pix_fmt="yuv420p")
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
        st.success("🔥 Render xong TOÀN TẬP! Hình, tiếng, chữ đủ cả! Xem ngay bên dưới!")
        
    except ffmpeg.Error as e:
        st.error(f"❌ Lỗi Render cuối cùng! Cỗ máy báo: {e.stderr.decode('utf8', errors='ignore') if e.stderr else str(e)}")