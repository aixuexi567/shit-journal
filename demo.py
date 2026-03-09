import os
import time
import re
import img2pdf
from PIL import Image
from playwright.sync_api import sync_playwright

URL = "https://shitjournal.org/preprints/279ca797-01e5-4270-b60d-758a1a3369d6"
OUTPUT_DIR = "paper_output"
IMG_DIR = os.path.join(OUTPUT_DIR, "images")


def ensure_dirs():
    if os.path.exists(IMG_DIR):
        # Clean up existing images to avoid mixing with old runs
        for f in os.listdir(IMG_DIR):
            if f.endswith(".png"):
                os.remove(os.path.join(IMG_DIR, f))
    os.makedirs(IMG_DIR, exist_ok=True)


def normalize_images_to_rgb(image_paths):
    fixed_paths = []
    for path in image_paths:
        try:
            img = Image.open(path).convert("RGB")
            img.save(path, "PNG")
            fixed_paths.append(path)
        except Exception as e:
            print(f"Error processing {path}: {e}")
    return fixed_paths


def make_pdf_from_images(image_paths, pdf_path):
    if not image_paths:
        print("No images to convert to PDF.")
        return
    try:
        with open(pdf_path, "wb") as f:
            f.write(img2pdf.convert(image_paths))
        print(f"[done] PDF 已生成: {pdf_path}")
    except Exception as e:
        print(f"Error generating PDF: {e}")


def handle_modal(page):
    print("[Modal] Checking for user agreement modal...")
    overlay = page.locator(".fixed.inset-0.z-\\[99999\\]")
    
    try:
        if overlay.is_visible(timeout=5000):
            print("[Modal] Modal detected.")
            checkbox = overlay.locator("input[type='checkbox']").first
            if checkbox.is_visible():
                print("[Modal] Clicking checkbox...")
                checkbox.click()
                time.sleep(0.5)
            
            btn = overlay.locator("button").last
            btn.wait_for(state="visible")
            time.sleep(0.5)
            
            if not btn.is_disabled():
                print("[Modal] Clicking confirm button...")
                btn.click()
                overlay.wait_for(state="hidden", timeout=10000)
                print("[Modal] Modal dismissed.")
            else:
                print("[Modal] Button is still disabled!")
        else:
            print("[Modal] No modal detected (timeout).")
            
    except Exception as e:
        print(f"[Modal] No modal or error handling it: {e}")


def sanitize_filename(name):
    # Remove invalid characters for filenames
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def get_paper_title(page):
    try:
        # Based on inspection, the title is in the first H2
        # Or we can look for specific text patterns if H2 is generic
        # H2 [0]: 21世纪南非LGBTQ群体的“钟摆式”发展
        h2 = page.locator("h2").first
        title = h2.text_content()
        if title:
            print(f"[Title] Found title: {title}")
            return title.strip()
    except Exception as e:
        print(f"[Title] Error extracting title: {e}")
    
    return "paper"


def main():
    ensure_dirs()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1600, "height": 2200},
            device_scale_factor=2
        )
        page = context.new_page()

        print(f"[1] 打开页面: {URL}")
        page.goto(URL, wait_until="networkidle", timeout=60000)
        time.sleep(3)
        
        handle_modal(page)
        
        # Get title after modal handling
        raw_title = get_paper_title(page)
        safe_title = sanitize_filename(raw_title)
        pdf_filename = f"{safe_title}.pdf"
        pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)
        print(f"[Config] Target PDF path: {pdf_path}")

        image_paths = []
        page_num = 1
        
        while True:
            print(f"[2] 处理第 {page_num} 页...")
            
            canvas = page.locator("canvas").first
            try:
                canvas.wait_for(state="visible", timeout=10000)
            except Exception as e:
                print(f"Wait for canvas failed: {e}")
                break
                
            time.sleep(2.0)
            
            out_path = os.path.join(IMG_DIR, f"page_{page_num:03d}.png")
            print(f"   - 截图保存到: {out_path}")
            
            try:
                canvas.screenshot(path=out_path)
                image_paths.append(out_path)
            except Exception as e:
                print(f"Screenshot failed: {e}")
                break

            next_btn = page.locator("button").filter(has_text="下一页 →").first
            
            if next_btn.count() == 0:
                print("   - 未找到'下一页'按钮，停止。")
                break
            
            if next_btn.is_disabled():
                print("   - '下一页'按钮已禁用，已到达最后一页。")
                break
            
            print("   - 点击下一页...")
            next_btn.scroll_into_view_if_needed()
            
            try:
                next_btn.click()
                page_num += 1
                time.sleep(2.0)
            except Exception as e:
                print(f"Click next failed: {e}")
                break

        print(f"[3] 收集到 {len(image_paths)} 张图片，开始转换 PDF...")
        if image_paths:
            fixed_paths = normalize_images_to_rgb(image_paths)
            make_pdf_from_images(fixed_paths, pdf_path)
        else:
            print("[error] 未收集到任何图片。")

        browser.close()


if __name__ == "__main__":
    main()
