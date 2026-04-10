import os
import streamlit as st
from utils import settings

# --- CHIÊU THỨC "BẤT TỬ" CỦA QUANG ICTU ---
# Thử import từng ông, nếu thiếu thì dùng Google TTS thay thế cho an toàn

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

# Luôn có Google TTS để "gánh team"
try:
    from gtts import gTTS as gTTS_lib
    class gTTS_wrapper:
        def run(self, text, filepath):
            tts = gTTS_lib(text=text, lang='vi') # Mặc định tiếng Việt
            tts.save(filepath)
    gTTS = gTTS_wrapper
    HAS_GTTS = True
except:
    gTTS = None
    HAS_GTTS = False

def save_text_to_mp3(reddit_obj):
    """Hàm tổng quản tạo giọng nói - Đảm bảo không bao giờ sập app"""
    try:
        tts_service = settings.config["settings"]["tts"]["voice_service"].lower()
    except:
        tts_service = "gtts"
    
    path = "assets/temp/mp3"
    os.makedirs(path, exist_ok=True)
    text = reddit_obj["thread_title"]
    filepath = f"{path}/title.mp3"

    # --- LOGIC CHỌN GIỌNG THÔNG MINH ---
    if tts_service == "elevenlabs" and HAS_ELEVENLABS:
        try:
            elevenlabs().run(text, filepath)
            st.success("🎙️ Đang dùng giọng ElevenLabs...")
            return 10.0, 0
        except: pass

    if tts_service == "tiktok" and HAS_TIKTOK:
        try:
            tiktok().run(text, filepath)
            st.success("🎙️ Đang dùng giọng TikTok...")
            return 10.0, 0
        except: pass

    # Cứu cánh cuối cùng: Google TTS
    if HAS_GTTS:
        gTTS().run(text, filepath)
        st.success("🎙️ Đã dùng giọng Google TTS thay thế!")
    else:
        st.error("❌ Lỗi: Không tìm thấy thư viện giọng đọc nào!")
    
    return 10.0, 0