from playwright.sync_api import sync_playwright
import time

def get_threads_content(url):
    """Hàm chuyên dụng để lấy chữ từ link Threads"""
    print(f"🔍 Đang truy cập: {url}")
    with sync_playwright() as p:
        # headless=True để chạy được trên server Streamlit
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # Truy cập link với thời gian chờ 60 giây
            page.goto(url, timeout=60000)
            time.sleep(5) # Đợi 5 giây để nội dung load hết
            
            # Tìm tất cả các thẻ span có chứa nội dung bài viết
            texts = page.locator('span[dir="auto"]').all_inner_texts()
            
            # Lọc các đoạn text có độ dài ý nghĩa (tránh lấy mấy cái chữ lặt vặt)
            content = " ".join([t for t in texts if len(t.strip()) > 10])
            return content
        except Exception as e:
            print(f"❌ Lỗi khi cào dữ liệu: {e}")
            return None
        finally:
            browser.close()
