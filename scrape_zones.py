import json
import time
import os
from playwright.sync_api import sync_playwright

BASE_URL = "https://shitjournal.org"
ZONES = ["stone", "septic", "latrine"]
OUTPUT_DIR = "data"

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

def scrape_zone(page, zone):
    start_url = f"https://shitjournal.org/preprints?zone={zone}"
    print(f"\n=== Scraping Zone: {zone} ===")
    print(f"Opening {start_url}")
    
    try:
        page.goto(start_url, wait_until="networkidle", timeout=60000)
    except Exception as e:
        print(f"Error loading zone {zone}: {e}")
        return []

    time.sleep(3)
    
    # Handle modal on the first load of a zone (though it might persist per session)
    handle_modal(page)

    all_papers = []
    page_idx = 1
    seen_urls = set()

    while True:
        print(f"--- Processing {zone} Page {page_idx} ---")
        
        try:
            page.wait_for_selector("a[href*='/preprints/']", timeout=10000)
        except:
            print(f"No papers found on page {page_idx} or timeout.")
            break
            
        time.sleep(2)
        
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
                "title": title,
                "zone": zone
            }
            current_page_papers.append(paper_info)
            all_papers.append(paper_info)
            # print(f"Found: {title[:30]}... -> {full_url}")

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
        try:
            next_btn.scroll_into_view_if_needed()
            next_btn.click()
            page_idx += 1
            time.sleep(3)
        except Exception as e:
            print(f"Error clicking next: {e}")
            break

    return all_papers

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        for zone in ZONES:
            papers = scrape_zone(page, zone)
            print(f"Total papers found in {zone}: {len(papers)}")
            
            output_file = os.path.join(OUTPUT_DIR, f"papers_{zone}.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(papers, f, ensure_ascii=False, indent=2)
            print(f"Saved list to {output_file}")
            
        browser.close()

if __name__ == "__main__":
    main()
