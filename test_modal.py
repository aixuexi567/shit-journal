from playwright.sync_api import sync_playwright

def test_interaction():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://shitjournal.org/preprints/279ca797-01e5-4270-b60d-758a1a3369d6")
        page.wait_for_timeout(5000)
        
        # Click checkbox
        page.locator("input[type='checkbox']").first.click()
        print("Checkbox clicked.")
        page.wait_for_timeout(1000)
        
        # Check button status
        btn = page.locator(".fixed.inset-0.z-\\[99999\\] button").last
        print(f"Button text: {btn.text_content()}")
        print(f"Button disabled: {btn.is_disabled()}")
        
        if not btn.is_disabled():
            btn.click()
            print("Button clicked.")
            page.wait_for_timeout(2000)
            # Check if overlay is gone
            overlay = page.locator(".fixed.inset-0.z-\\[99999\\]")
            if overlay.count() == 0 or not overlay.is_visible():
                print("Overlay gone.")
            else:
                print("Overlay still present.")
        
        browser.close()

if __name__ == "__main__":
    test_interaction()
