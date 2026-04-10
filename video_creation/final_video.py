import multiprocessing
import os
import re
import tempfile
import textwrap
import threading
import time
from os.path import exists
from pathlib import Path
from typing import Dict, Tuple # Đã xóa Final để không bị lỗi Type Hint

import ffmpeg
import translators
from PIL import Image, ImageDraw, ImageFont
from rich.console import Console
from rich.progress import track

from utils import settings
from utils.cleanup import cleanup
from utils.console import print_step, print_substep
from utils.fonts import getheight
from utils.id import extract_id
from utils.thumbnail import create_thumbnail
from utils.videos import save_data

console = Console()

class ProgressFfmpeg(threading.Thread):
    def __init__(self, vid_duration_seconds, progress_update_callback):
        threading.Thread.__init__(self, name="ProgressFfmpeg")
        self.stop_event = threading.Event()
        self.output_file = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        self.vid_duration_seconds = vid_duration_seconds
        self.progress_update_callback = progress_update_callback

    def run(self):
        while not self.stop_event.is_set():
            latest_progress = self.get_latest_ms_progress()
            if latest_progress is not None:
                completed_percent = latest_progress / self.vid_duration_seconds
                self.progress_update_callback(completed_percent)
            time.sleep(1)

    def get_latest_ms_progress(self):
        lines = self.output_file.readlines()
        if lines:
            for line in lines:
                if "out_time_ms" in line:
                    out_time_ms_str = line.split("=")[1].strip()
                    if out_time_ms_str.isnumeric():
                        return float(out_time_ms_str) / 1000000.0
                    else:
                        return None
        return None

    def stop(self):
        self.stop_event.set()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args, **kwargs):
        self.stop()

def name_normalize(name: str) -> str:
    name = re.sub(r'[?\\"%*:|<>]', "", name)
    name = re.sub(r"( [w,W]\s?\/\s?[o,O,0])", r" without", name)
    name = re.sub(r"( [w,W]\s?\/)", r" with", name)
    name = re.sub(r"(\d+)\s?\/\s?(\d+)", r"\1 of \2", name)
    name = re.sub(r"(\w+)\s?\/\s?(\w+)", r"\1 or \2", name)
    name = re.sub(r"\/", r"", name)

    try:
        lang = settings.config.get("reddit", {}).get("thread", {}).get("post_lang", "")
        if lang:
            print_substep("Translating filename...")
            translated_name = translators.translate_text(name, translator="google", to_language=lang)
            return translated_name
    except Exception:
        pass
    return name

def prepare_background(reddit_id: str, W: int, H: int) -> str:
    output_path = f"assets/temp/{reddit_id}/background_noaudio.mp4"
    output = (
        ffmpeg.input(f"assets/temp/{reddit_id}/background.mp4")
        .filter("crop", f"ih*({W}/{H})", "ih")
        .output(
            output_path,
            an=None,
            **{
                "c:v": "libx264", # QUAN TRỌNG: Đổi từ h264_nvenc sang libx264 để chạy được trên Streamlit Cloud
                "b:v": "10M",     # Giảm bitrate xuống 10M cho nhẹ server
                "threads": multiprocessing.cpu_count(),
            },
        )
        .overwrite_output()
    )
    try:
        output.run(quiet=True)
    except ffmpeg.Error as e:
        print(e.stderr.decode("utf8"))
    return output_path

def get_text_height(draw, text, font, max_width):
    lines = textwrap.wrap(text, width=max_width)
    total_height = 0
    for line in lines:
        _, _, _, height = draw.textbbox((0, 0), line, font=font)
        total_height += height
    return total_height

def create_fancy_thumbnail(image, text, text_color, padding, wrap=35):
    print_step(f"Creating fancy thumbnail for: {text}")
    font_title_size = 47
    font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), font_title_size)
    image_width, image_height = image.size

    draw = ImageDraw.Draw(image)
    text_height = get_text_height(draw, text, font, wrap)
    lines = textwrap.wrap(text, width=wrap)
    new_image_height = image_height + text_height + padding * (len(lines) - 1) - 50

    top_part_height = image_height // 2
    middle_part_height = 1
    bottom_part_height = image_height - top_part_height - middle_part_height

    top_part = image.crop((0, 0, image_width, top_part_height))
    middle_part = image.crop((0, top_part_height, image_width, top_part_height + middle_part_height))
    bottom_part = image.crop((0, top_part_height + middle_part_height, image_width, image_height))

    new_middle_height = new_image_height - top_part_height - bottom_part_height
    middle_part = middle_part.resize((image_width, new_middle_height))

    new_image = Image.new("RGBA", (image_width, new_image_height))
    new_image.paste(top_part, (0, 0))
    new_image.paste(middle_part, (0, top_part_height))
    new_image.paste(bottom_part, (0, top_part_height + new_middle_height))

    draw = ImageDraw.Draw(new_image)
    y = top_part_height + padding
    for line in lines:
        draw.text((120, y), line, font=font, fill=text_color, align="left")
        y += get_text_height(draw, line, font, wrap) + padding

    username_font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), 30)
    try:
        channel_name = settings.config.get("settings", {}).get("channel_name", "@ThreadsBot")
    except Exception:
        channel_name = "@ThreadsBot"

    draw.text((205, 825), channel_name, font=username_font, fill=text_color, align="left")
    return new_image

def merge_background_audio(audio: ffmpeg, reddit_id: str):
    try:
        background_audio_volume = settings.config.get("settings", {}).get("background", {}).get("background_audio_volume", 0.15)
    except Exception:
        background_audio_volume = 0.15

    if background_audio_volume == 0:
        return audio
    else:
        bg_audio_path = f"assets/temp/{reddit_id}/background.mp3"
        if not os.path.exists(bg_audio_path) or os.path.getsize(bg_audio_path) == 0:
            return audio
            
        bg_audio = ffmpeg.input(bg_audio_path).filter("volume", background_audio_volume)
        merged_audio = ffmpeg.filter([audio, bg_audio], "amix", duration="longest")
        return merged_audio

def make_final_video(number_of_clips: int, length: int, reddit_obj: dict, background_config: Dict[str, Tuple]):
    # --- ĐẠI PHẪU TYPE HINTING CHO QUANG ICTU ---
    try:
        conf = settings.config.get("settings", {})
        W = int(conf.get("resolution_w", 1080))
        H = int(conf.get("resolution_h", 1920))
        opacity = float(conf.get("opacity", 0.9))
        
        bg_conf = conf.get("background", {})
        allowOnlyTTSFolder = bool(bg_conf.get("enable_extra_audio", False) and bg_conf.get("background_audio_volume", 0) != 0)
    except Exception:
        W, H = 1080, 1920
        opacity = 0.9
        allowOnlyTTSFolder = False

    reddit_id = extract_id(reddit_obj)
    print_step("Creating the final video 🎥")

    bg_video_path = f"assets/temp/{reddit_id}/background.mp4"
    if not os.path.exists(bg_video_path) or os.path.getsize(bg_video_path) == 0:
        print_step("❌ Video nền không tồn tại. Bỏ qua bước Render.")
        return

    background_clip = ffmpeg.input(prepare_background(reddit_id, W=W, H=H))

    # Xử lý Audio
    audio_clips = list()
    storymode = settings.config.get("settings", {}).get("storymode", False)
    
    if storymode:
        storymodemethod = settings.config.get("settings", {}).get("storymodemethod", 0)
        if storymodemethod == 0:
            audio_clips = [ffmpeg.input(f"assets/temp/{reddit_id}/mp3/title.mp3")]
            audio_clips.insert(1, ffmpeg.input(f"assets/temp/{reddit_id}/mp3/postaudio.mp3"))
        elif storymodemethod == 1:
            audio_clips = [ffmpeg.input(f"assets/temp/{reddit_id}/mp3/postaudio-{i}.mp3") for i in track(range(number_of_clips + 1), "Collecting the audio files...")]
            audio_clips.insert(0, ffmpeg.input(f"assets/temp/{reddit_id}/mp3/title.mp3"))
    else:
        audio_clips = [ffmpeg.input(f"assets/temp/{reddit_id}/mp3/{i}.mp3") for i in range(number_of_clips)]
        audio_clips.insert(0, ffmpeg.input(f"assets/temp/{reddit_id}/mp3/title.mp3"))

    audio_concat = ffmpeg.concat(*audio_clips, a=1, v=0)
    ffmpeg.output(audio_concat, f"assets/temp/{reddit_id}/audio.mp3", **{"b:a": "192k"}).overwrite_output().run(quiet=True)

    screenshot_width = int((W * 90) // 100) # Phóng to ảnh lên 90% chiều rộng video cho dễ đọc
    audio = ffmpeg.input(f"assets/temp/{reddit_id}/audio.mp3")
    final_audio = merge_background_audio(audio, reddit_id)

    image_clips = list()
    Path(f"assets/temp/{reddit_id}/png").mkdir(parents=True, exist_ok=True)
    title_template = Image.open("assets/title_template.png")
    title = name_normalize(reddit_obj["thread_title"])
    title_img = create_fancy_thumbnail(title_template, title, "#000000", 5)
    title_img.save(f"assets/temp/{reddit_id}/png/title.png")
    
    image_clips.insert(0, ffmpeg.input(f"assets/temp/{reddit_id}/png/title.png")["v"].filter("scale", screenshot_width, -1))
    
    # Do Threads Bot hiện tại chỉ dùng Title, không dùng comments nên mình ghép thẳng
    image_overlay = image_clips[0].filter("colorchannelmixer", aa=opacity)
    background_clip = background_clip.overlay(
        image_overlay,
        enable=f"between(t,0,{length})",
        x="(main_w-overlay_w)/2",
        y="(main_h-overlay_h)/2",
    )

    title_thumb = reddit_obj["thread_title"]
    filename = f"{name_normalize(title)[:251]}"

    # --- ĐỒNG BỘ THƯ MỤC VỚI STREAMLIT ---
    defaultPath = "video_output"
    if not exists(defaultPath):
        os.makedirs(defaultPath)

    text = f"Rendered by Quang - ICTU"
    background_clip = ffmpeg.drawtext(
        background_clip,
        text=text,
        x=f"(w-text_w)/2",
        y=f"(h-text_h-50)",
        fontsize=40,
        fontcolor="White",
        fontfile=os.path.join("fonts", "Roboto-Bold.ttf"),
    )
    
    print_step("Rendering the video 🎥")
    
    path = f"{defaultPath}/{filename}.mp4"
    try:
        ffmpeg.output(
            background_clip,
            final_audio,
            path,
            f="mp4",
            **{
                "c:v": "libx264", # Chạy bằng CPU trên Streamlit
                "b:v": "10M",
                "b:a": "192k",
                "threads": multiprocessing.cpu_count(),
                "preset": "fast" # Giúp Render nhanh hơn trên máy chủ yếu
            },
        ).overwrite_output().run(quiet=True)
    except ffmpeg.Error as e:
        print(e.stderr.decode("utf8"))

    print_step("Done! 🎉 The video is ready to view.")