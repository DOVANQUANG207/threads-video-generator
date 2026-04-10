import random
import os

# --- CHIÊU THỨC SAFE IMPORT CỦA ANH EM ICTU ---
try:
    from elevenlabs import save
    from elevenlabs.client import ElevenLabs
    HAS_ELEVENLABS = True
except ImportError:
    HAS_ELEVENLABS = False

from utils import settings

class elevenlabs:
    def __init__(self):
        self.max_chars = 2500
        self.client = None

    def run(self, text, filepath, random_voice: bool = False):
        # Nếu không có thư viện, báo lỗi nhẹ nhàng thay vì làm sập app
        if not HAS_ELEVENLABS:
            print("⚠️ ElevenLabs chưa được cài đặt hoặc bị lỗi Pydantic. Đang bỏ qua...")
            return False

        if self.client is None:
            self.initialize()
            
        try:
            if random_voice:
                voice = self.randomvoice()
            else:
                voice = str(settings.config["settings"]["tts"]["elevenlabs_voice_name"]).capitalize()

            audio = self.client.generate(text=text, voice=voice, model="eleven_multilingual_v1")
            save(audio=audio, filename=filepath)
            return True
        except Exception as e:
            print(f"❌ Lỗi ElevenLabs: {e}")
            return False

    def initialize(self):
        if not HAS_ELEVENLABS:
            return

        if settings.config["settings"]["tts"]["elevenlabs_api_key"]:
            api_key = settings.config["settings"]["tts"]["elevenlabs_api_key"]
        else:
            # Thay vì báo lỗi sập app, mình chỉ in ra cảnh báo
            print("⚠️ Chưa có ElevenLabs API Key.")
            return

        try:
            self.client = ElevenLabs(api_key=api_key)
        except Exception:
            self.client = None

    def randomvoice(self):
        if not HAS_ELEVENLABS or self.client is None:
            return "Adam" # Trả về tên mặc định nếu lỗi
        try:
            return random.choice(self.client.voices.get_all().voices).name
        except Exception:
            return "Adam"