import os
import streamlit as st
from utils import settings

# --- CHIÊU THỨC "DỌN ĐƯỜNG" CỦA QUANG ICTU ---
# Thử import từng ông, ông nào thiếu thì cho qua để app không sập

try:
    from TTS.elevenlabs import elevenlabs
    HAS_ELEVENLABS = True
except:
    elevenlabs = None
    HAS_ELEVENLABS = False

try:
    from TTS.tiktok import tiktok
    HAS_TIKTOK = True
except:
    tiktok = None
    HAS_TIKTOK = False

# Đối với Google TTS (gTTS)
try:
    # Thử lấy từ thư mục TTS nếu có file wrapper
    from TTS.gTTS import gTTS
    HAS_GTTS = True
except:
    # Nếu không có file TTS/gTTS.py, ta tự tạo một class dùng thư viện gtts gốc
    try:
        from gtts import gTTS as gTTS_lib
        class gTTS_wrapper:
            def run(self, text, filepath):
                tts = gTTS_lib(text=text, lang='vi') # Mặc định tiếng Việt cho Threads VN
                tts.save(filepath)
        gTTS = gTTS_wrapper
        HAS_GTTS = True
    except:
        gTTS = None
        HAS_GTTS = False

def save_text_to_mp3(reddit_obj):
    """Hàm tổng quản tạo giọng nói - Đã fix lỗi module missing"""
    
    # Mặc định dùng Google cho an toàn nhất
    tts_service = "gtts" 
    
    path = "assets/temp/mp3"
    os.makedirs(path, exist_ok=True)
    text = reddit_obj["thread_title"]
    filepath = f"{path}/title.mp3"

    # --- CHỌN ĐỘNG CƠ CHẠY ---
    if tts_service == "elevenlabs" and HAS_ELEVENLABS:
        elevenlabs().run(text, filepath)
    elif tts_service == "tiktok" and HAS_TIKTOK:
        tiktok().run(text, filepath)
    elif HAS_GTTS:
        # Google TTS là lựa chọn bền bỉ nhất
        gTTS().run(text, filepath)
    else:
        st.error("❌ Không tìm thấy động cơ giọng đọc nào cả! Quang check lại thư mục TTS nhé.")
        return 0, 0

    return 10.0, 0