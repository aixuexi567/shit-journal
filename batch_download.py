import json
import os
import time
import re
import img2pdf
from PIL import Image
from playwright.sync_api import sync_playwright

INPUT_FILE = "papers_list.json"
OUTPUT_DIR = "paper_output"
IMG_DIR = os.path.join(OUTPUT_DIR, "images")

def ensure_dirs():
    # Only clean if we are starting a fresh paper
    # But since we reuse this dir for each paper, we should clean it before each paper
    if os.path.exists(IMG_DIR):
        for f in os.listdir(IMG_DIR):
            if f.endswith(".png"):
                os.remove(os.path.join(IMG_DIR, f))
    os.makedirs(IMG_DIR, exist_ok=True)

def sanitize_filename(name):
    # Remove emojis and special chars
    name = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    return name

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
        return False
    try:
        with open(pdf_path, "wb") as f:
            f.write(img2pdf.convert(image_paths))
        return True
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False

def handle_modal(page):
    # Only check if modal is present
    try:
        overlay = page.locator(".fixed.inset-0.z-\\[99999\\]")
        if overlay.count() > 0 and overlay.is_visible(timeout=2000):
            # print("[Modal] Detected.")
            checkbox = overlay.locator("input[type='checkbox']").first
            if checkbox.is_visible():
                checkbox.click()
                time.sleep(0.5)
            
            btn = overlay.locator("button").last
            if btn.is_visible() and not btn.is_disabled():
                btn.click()
                overlay.wait_for(state="hidden", timeout=5000)
                # print("[Modal] Dismissed.")
    except Exception:
        pass

def check_not_found(page):
    try:
        # Check title or h1/h2 or body text for "Not Found" indicators
        # Common patterns: "404 Not Found", "Page Not Found", "未找到"
        
        # 1. Check page title
        page_title = page.title()
        if "404" in page_title or "Not Found" in page_title:
            return True

        # 2. Check main heading
        h1 = page.locator("h1").first
        if h1.count() > 0:
            h1_text = h1.text_content()
            if h1_text and ("Not Found" in h1_text or "未找到" in h1_text):
                return True
                
        # 3. Check body text (last resort, checking first few chars)
        body_text = page.locator("body").text_content()
        if body_text:
             if "404 Not Found" in body_text or "页面未找到" in body_text:
                 return True
                 
        return False
    except Exception:
        return False

def process_paper(page, url, raw_title):
    print(f"Processing: {url}")
    
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(2) # Wait for render
    except Exception as e:
        print(f"Failed to load page: {e}")
        return

    # Check for Not Found
    if check_not_found(page):
        print("  [Skip] Paper not found (404/Not Found detected).")
        return

    handle_modal(page)

    # Get title from H2
    try:
        h2 = page.locator("h2").first
        if h2.count() > 0:
            final_title = h2.text_content().strip()
            # print(f"  Title: {final_title}")
        else:
            final_title = raw_title
    except:
        final_title = raw_title

    safe_title = sanitize_filename(final_title)
    if len(safe_title) > 100:
        safe_title = safe_title[:100]
        
    pdf_path = os.path.join(OUTPUT_DIR, f"{safe_title}.pdf")
    
    if os.path.exists(pdf_path):
        print(f"  [Skip] Already exists: {pdf_path}")
        return

    print(f"  Downloading: {safe_title}")

    # Clear temp images
    ensure_dirs()
    
    image_paths = []
    page_num = 1
    
    while True:
        canvas = page.locator("canvas").first
        try:
            canvas.wait_for(state="visible", timeout=5000)
        except:
            print("  No canvas found, maybe text only or error.")
            break
            
        time.sleep(1.0) # Wait for canvas to draw
        
        out_path = os.path.join(IMG_DIR, f"temp_{page_num:03d}.png")
        try:
            canvas.screenshot(path=out_path)
            image_paths.append(out_path)
            # print(f"  - Page {page_num} captured.")
        except Exception as e:
            print(f"  Screenshot failed: {e}")
            break

        # Check Next Button
        # Button text: "下一页 →"
        next_btn = page.locator("button").filter(has_text="下一页 →").first
        
        if next_btn.count() == 0:
            break
            
        if next_btn.is_disabled():
            break
        
        try:
            next_btn.scroll_into_view_if_needed()
            next_btn.click()
            page_num += 1
            time.sleep(1.5)
        except:
            break

    if image_paths:
        fixed_paths = normalize_images_to_rgb(image_paths)
        if make_pdf_from_images(fixed_paths, pdf_path):
            print(f"  [Done] Saved PDF: {pdf_path}")
    else:
        print("  [Warn] No images captured for this paper.")

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"File {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        papers = json.load(f)

    print(f"Total papers to process: {len(papers)}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1600, "height": 2200},
            device_scale_factor=2
        )
        page = context.new_page()

        for i, paper in enumerate(papers):
            print(f"[{i+1}/{len(papers)}]")
            process_paper(page, paper["url"], paper.get("title", "Unknown"))
            
        browser.close()

if __name__ == "__main__":
    main()
