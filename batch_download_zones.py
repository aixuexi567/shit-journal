import json
import os
import time
import re
import img2pdf
from PIL import Image
from playwright.sync_api import sync_playwright

INPUT_DIR = "data"
OUTPUT_DIR = "paper_output"
ZONES = ["stone", "septic", "latrine"]

def ensure_dirs(img_dir):
    if os.path.exists(img_dir):
        # We don't want to delete existing images if we are resuming or if they are valid
        # But for a clean run per paper, we might want to ensure it's clean
        # Since we are creating a unique dir per paper now, we just make sure it exists
        pass
    os.makedirs(img_dir, exist_ok=True)

def sanitize_filename(name):
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
    try:
        overlay = page.locator(".fixed.inset-0.z-\\[99999\\]")
        if overlay.count() > 0 and overlay.is_visible(timeout=2000):
            checkbox = overlay.locator("input[type='checkbox']").first
            if checkbox.is_visible():
                checkbox.click()
                time.sleep(0.5)
            
            btn = overlay.locator("button").last
            if btn.is_visible() and not btn.is_disabled():
                btn.click()
                overlay.wait_for(state="hidden", timeout=5000)
    except Exception:
        pass

def remove_watermark(page):
    try:
        page.evaluate("""
            () => {
                const watermarks = document.querySelectorAll('.absolute.inset-0.z-10.pointer-events-none.overflow-hidden');
                watermarks.forEach(el => el.style.display = 'none');
                
                document.querySelectorAll('div, span').forEach(el => {
                    if (el.innerText && el.innerText.includes('S.H.I.T JOURNAL PREPRINT')) {
                         el.style.display = 'none';
                    }
                });
            }
        """)
    except Exception as e:
        print(f"  [Watermark] Removal failed: {e}")

def check_not_found(page):
    try:
        page_title = page.title()
        if "404" in page_title or "Not Found" in page_title:
            return True

        h1 = page.locator("h1").first
        if h1.count() > 0:
            h1_text = h1.text_content()
            if h1_text and ("Not Found" in h1_text or "未找到" in h1_text):
                return True
                
        body_text = page.locator("body").text_content()
        if body_text:
             if "404 Not Found" in body_text or "页面未找到" in body_text:
                 return True
                 
        return False
    except Exception:
        return False

def process_paper(page, url, raw_title, zone_output_dir):
    print(f"Processing: {url}")
    
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(2)
    except Exception as e:
        print(f"Failed to load page: {e}")
        return

    if check_not_found(page):
        print("  [Skip] Paper not found.")
        return

    handle_modal(page)
    remove_watermark(page)

    try:
        h2 = page.locator("h2").first
        if h2.count() > 0:
            final_title = h2.text_content().strip()
        else:
            final_title = raw_title
    except:
        final_title = raw_title

    safe_title = sanitize_filename(final_title)
    if len(safe_title) > 100:
        safe_title = safe_title[:100]
    
    # Create a specific folder for this paper
    paper_dir = os.path.join(zone_output_dir, safe_title)
    ensure_dirs(paper_dir)
        
    pdf_path = os.path.join(paper_dir, f"{safe_title}.pdf")
    
    # Force overwrite if we want to ensure watermark removal and image saving
    # If PDF exists but we want to ensure images are there too, we might need to check images?
    # For now, let's assume if PDF exists in this NEW structure (folder per paper), it's done.
    # But user might be running this again to get images for existing PDFs.
    # So we should check if images exist. If not, re-run.
    
    # Simple check: if PDF exists, assume done.
    # Wait, the user asked to "also save images". If I skip existing PDFs, I might miss saving images for them if they were downloaded before without images.
    # The previous run put PDFs directly in zone folder. Now we put them in a subfolder.
    # So the path `paper_output/zone/Title/Title.pdf` likely doesn't exist yet.
    # So it will re-download, which is good.
    
    if os.path.exists(pdf_path):
         print(f"  [Skip] Already exists: {pdf_path}")
         return

    print(f"  Downloading to: {paper_dir}")

    image_paths = []
    page_num = 1
    
    while True:
        remove_watermark(page)
        
        canvas = page.locator("canvas").first
        try:
            canvas.wait_for(state="visible", timeout=5000)
        except:
            print("  No canvas found.")
            break
            
        time.sleep(1.0)
        
        # Save image with a clean name in the paper's folder
        out_path = os.path.join(paper_dir, f"page_{page_num:03d}.png")
        try:
            canvas.screenshot(path=out_path)
            image_paths.append(out_path)
        except Exception as e:
            print(f"  Screenshot failed: {e}")
            break

        next_btn = page.locator("button").filter(has_text="下一页 →").first
        
        if next_btn.count() == 0 or next_btn.is_disabled():
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
            print(f"  [Done] Saved PDF and {len(image_paths)} images.")
    else:
        print("  [Warn] No images captured.")

def main():
    if not os.path.exists(INPUT_DIR):
        print(f"Directory {INPUT_DIR} not found.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1600, "height": 2200},
            device_scale_factor=2
        )
        page = context.new_page()

        for zone in ZONES:
            input_file = os.path.join(INPUT_DIR, f"papers_{zone}.json")
            if not os.path.exists(input_file):
                continue
                
            with open(input_file, "r", encoding="utf-8") as f:
                papers = json.load(f)
            
            print(f"\n=== Processing Zone: {zone} ({len(papers)} papers) ===")
            
            zone_output_dir = os.path.join(OUTPUT_DIR, zone)
            os.makedirs(zone_output_dir, exist_ok=True)
            
            for i, paper in enumerate(papers):
                print(f"[{i+1}/{len(papers)}]")
                process_paper(page, paper["url"], paper.get("title", "Unknown"), zone_output_dir)
                
        browser.close()

if __name__ == "__main__":
    main()
