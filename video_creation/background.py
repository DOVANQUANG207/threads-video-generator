import os, re, random
from pathlib import Path
from random import randrange
import streamlit as st
from moviepy import AudioFileClip, VideoFileClip

def get_start_and_end_times(v_len, c_len):
    if int(c_len) <= int(v_len): return 0, int(c_len)
    max_s = max(0, int(c_len) - int(v_len) - 5)
    r_t = randrange(0, max_s) if max_s > 0 else 0
    return r_t, r_t + v_len

def get_background_config(mode): return ("url", "v.mp4", "cre", "center")
def download_background_video(c): pass
def download_background_audio(c): pass

def chop_background(background_config, video_length, reddit_object):
    t_id = re.sub(r"[^\w\s-]", "", reddit_object["thread_id"])
    temp_path = f"assets/temp/{t_id}"
    os.makedirs(temp_path, exist_ok=True)

    # 1. AUDIO
    try:
        a_dir = Path("assets/backgrounds/audio")
        auds = [str(f) for f in a_dir.glob("*.mp3") if f.stat().st_size > 500]
        if auds:
            with AudioFileClip(auds[0]) as b_audio:
                s, e = get_start_and_end_times(video_length, b_audio.duration)
                b_audio.subclipped(s, e).write_audiofile(f"{temp_path}/background.mp3", logger=None)
    except: pass

    # 2. VIDEO (CÓ TÚI KHÍ AN TOÀN)
    v_dir = Path("assets/backgrounds/video")
    vids = [str(f) for f in v_dir.glob("*.mp4")]
    
    if not vids:
        st.error("❌ Không thấy file .mp4 nào trong assets/backgrounds/video!")
        return False

    video_path = os.path.abspath(vids[0])
    
    # Bắt lỗi OSError do file hỏng (moov atom not found)
    try:
        with VideoFileClip(video_path) as video:
            start, end = get_start_and_end_times(video_length, video.duration)
            new_video = video.subclipped(start, end)
            new_video.write_videofile(f"{temp_path}/background.mp4", codec="libx264", audio=False, logger=None)
        return True
    except OSError as e:
        st.error(f"❌ File video bị hỏng rỗng ruột (Lỗi FFmpeg). Hãy lên GitHub Web, xóa file {vids[0]} và Upload trực tiếp file video xịn vào!")
        return False
    except Exception as e:
        st.error(f"❌ Lỗi đọc video: {e}")
        return False