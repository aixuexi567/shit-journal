from playwright.sync_api import sync_playwright

def inspect_content():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://shitjournal.org/preprints/279ca797-01e5-4270-b60d-758a1a3369d6")
        page.wait_for_timeout(5000)
        
        # Look for h2, h3 or specific classes
        print("--- H2 Elements ---")
        h2s = page.locator("h2").all()
        for i, h2 in enumerate(h2s):
            print(f"[{i}]: {h2.text_content()}")

        print("\n--- H3 Elements ---")
        h3s = page.locator("h3").all()
        for i, h3 in enumerate(h3s):
            print(f"[{i}]: {h3.text_content()}")
            
        print("\n--- Large Text Elements ---")
        # Try to find large text that might be the title
        large_texts = page.evaluate("""
            Array.from(document.querySelectorAll('*'))
                .filter(el => {
                    const style = window.getComputedStyle(el);
                    return parseFloat(style.fontSize) > 20 && el.innerText.length > 10;
                })
                .map(el => ({ tag: el.tagName, text: el.innerText.substring(0, 50), size: window.getComputedStyle(el).fontSize }))
        """)
        for item in large_texts:
            print(item)
            
        browser.close()

if __name__ == "__main__":
    inspect_content()
