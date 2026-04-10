# 🧵 Threads Video Maker Bot - By Quang

Công cụ tự động hóa quy trình tạo video TikTok/Shorts/Reels từ các bài viết trên **Threads**. Đây là phiên bản được tùy chỉnh và phát triển bởi **Quang** (ICTU), chuyển đổi từ lõi Reddit sang nền tảng Threads đầy tiềm năng.

## 🚀 Tính năng chính
- **Threads Scraper:** Tự động quét và lấy nội dung từ bất kỳ link Threads nào bằng Playwright.
- **Dynamic Image Creation:** Tự động vẽ giao diện bài viết Threads chuyên nghiệp để chèn vào video.
- **Text-to-Speech (TTS):** Chuyển đổi nội dung bài viết thành giọng nói tự nhiên.
- **Background Video:** Tự động tải và cắt ghép video nền (Minecraft parkour, GTA, v.v.).
- **Auto Rendering:** Xuất video hoàn chỉnh với phụ đề và âm nhạc chỉ trong vài phút.

## 🛠️ Công nghệ sử dụng
- **Ngôn ngữ:** Python 3.10+
- **Thư viện chính:** - `Playwright` (Cào dữ liệu & Chụp ảnh giao diện)
  - `MoviePy` & `FFmpeg` (Xử lý và biên tập video)
  - `Edge-TTS` / `gTTS` (Tạo giọng đọc)
  - `Streamlit` (Giao diện quản lý trên web)

## 📂 Cấu trúc dự án
- `main.py`: Luồng xử lý chính của Bot.
- `threads_scraper.py`: Module chuyên dụng để cào dữ liệu từ Threads.net.
- `video_creation/`: Chứa các hàm xử lý kỹ thuật về hình ảnh và video.
- `utils/`: Các công cụ hỗ trợ cài đặt và cấu hình hệ thống.

## ⚙️ Cài đặt & Sử dụng

### 1. Cài đặt môi trường
```bash
pip install -r requirements.txt
playwright install chromium
