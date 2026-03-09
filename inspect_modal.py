from playwright.sync_api import sync_playwright

def inspect_modal():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://shitjournal.org/preprints/279ca797-01e5-4270-b60d-758a1a3369d6")
        page.wait_for_timeout(5000)
        
        # Look for the overlay
        overlay = page.locator(".fixed.inset-0.z-\\[99999\\]")
        if overlay.count() > 0:
            print("Overlay found.")
            
            # Look for inputs inside the overlay
            inputs = overlay.locator("input").all()
            for i, inp in enumerate(inputs):
                print(f"Input [{i}]: type={inp.get_attribute('type')}, id={inp.get_attribute('id')}")
            
            # Look for the disabled button
            btn = overlay.locator("button").last
            print(f"Button text: {btn.text_content()}")
            
        browser.close()

if __name__ == "__main__":
    inspect_modal()
