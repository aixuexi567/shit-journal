from playwright.sync_api import sync_playwright

def inspect_list():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://shitjournal.org/preprints?zone=stone")
        page.wait_for_timeout(5000)
        
        # Check links that look like papers
        print("--- Potential Paper Links ---")
        links = page.locator("a").all()
        for i, link in enumerate(links):
            href = link.get_attribute("href")
            text = link.text_content()
            if href and "/preprints/" in href:
                print(f"[{i}] Text: {text[:50].strip()}... | Href: {href}")
        
        # Check pagination buttons
        print("\n--- Pagination Buttons ---")
        buttons = page.locator("button").all()
        for i, btn in enumerate(buttons):
            print(f"[{i}] Text: {btn.text_content()} | Disabled: {btn.is_disabled()}")

        browser.close()

if __name__ == "__main__":
    inspect_list()
