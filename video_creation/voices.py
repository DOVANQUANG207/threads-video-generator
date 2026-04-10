import os
import streamlit as st
from utils import settings

# --- 1. IMPORT AN TOÀN (CHẶN LỖI PYDANTIC) ---
try:
    from TTS.elevenlabs import elevenlabs
    HAS_ELEVENLABS = True
except (ImportError, Exception):
    elevenlabs = None
    HAS_ELEVENLABS = False

from TTS.tiktok import tiktok
from TTS.gTTS import gTTS

def save_text_to_mp3(reddit_obj):
    """Hàm tổng quản tạo giọng nói - Đã được Quang ICTU độ lại"""
    
    # Lấy cấu hình từ file config
    tts_service = settings.config["settings"]["tts"]["voice_service"].lower()
    
    # Check nếu đang chọn ElevenLabs mà trên mây không chạy được
    if tts_service == "elevenlabs" and not HAS_ELEVENLABS:
        if "STREAMLIT_SERVER_PORT" in os.environ:
            st.warning("⚠️ ElevenLabs lỗi thư viện trên Streamlit. Đang dùng tạm Google TTS nhé Quang!")
        tts_service = "gtts"

    # Đường dẫn lưu file audio
    path = "assets/temp/mp3"
    os.makedirs(path, exist_ok=True)
    
    text = reddit_obj["thread_title"]
    filepath = f"{path}/title.mp3"

    # --- 2. KÍCH HOẠT ĐỘNG CƠ (THAY CHO CHỮ PASS) ---
    if tts_service == "elevenlabs" and HAS_ELEVENLABS:
        st.write("🎙️ Đang dùng giọng xịn ElevenLabs...")
        elevenlabs().run(text, filepath)
    elif tts_service == "tiktok":
        st.write("🎙️ Đang dùng giọng TikTok...")
        tiktok().run(text, filepath)
    else:
        # Mặc định dùng Google TTS cực bền
        st.write("🎙️ Đang dùng giọng Google TTS...")
        gTTS().run(text, filepath)

    # Trả về độ dài (tạm tính) và số comment (Threads này là 0)
    # Vì Bot cần biết độ dài để cắt video, mình trả về giá trị tượng trưng
    return 10.0, 0