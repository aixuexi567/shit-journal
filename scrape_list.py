import json
import time
from playwright.sync_api import sync_playwright

BASE_URL = "https://shitjournal.org"
START_URL = "https://shitjournal.org/preprints?zone=stone"
OUTPUT_FILE = "papers_list.json"

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

def scrape_papers():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"Opening {START_URL}")
        page.goto(START_URL, wait_until="networkidle")
        time.sleep(3)
        
        # Handle the modal first
        handle_modal(page)

        all_papers = []
        page_idx = 1
        
        seen_urls = set()

        while True:
            print(f"--- Processing List Page {page_idx} ---")
            
            # Wait for list to load
            page.wait_for_selector("a[href*='/preprints/']")
            time.sleep(2) # Extra stability
            
            links = page.locator("a[href*='/preprints/']").all()
            
            current_page_papers = []

            for link in links:
                href = link.get_attribute("href")
                text = link.text_content()
                
                if not href:
                    continue
                    
                full_url = BASE_URL + href if href.startswith("/") else href
                
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                
                title = text.strip().replace('\n', ' ')
                
                paper_info = {
                    "url": full_url,
                    "title": title
                }
                current_page_papers.append(paper_info)
                all_papers.append(paper_info)
                print(f"Found: {title[:30]}... -> {full_url}")

            print(f"Page {page_idx}: Found {len(current_page_papers)} papers.")

            # Pagination
            next_btn = page.locator("button").filter(has_text="Next").first
            
            if next_btn.count() == 0:
                print("Next button not found. Stopping.")
                break
                
            if next_btn.is_disabled():
                print("Next button disabled. Reached last page.")
                break
                
            print("Clicking Next...")
            next_btn.scroll_into_view_if_needed()
            next_btn.click()
            page_idx += 1
            
            time.sleep(3)

        print(f"Total papers found: {len(all_papers)}")
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_papers, f, ensure_ascii=False, indent=2)
        print(f"Saved list to {OUTPUT_FILE}")
        
        browser.close()

if __name__ == "__main__":
    scrape_papers()
