from playwright.sync_api import sync_playwright

def inspect_watermark_refined():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://shitjournal.org/preprints/279ca797-01e5-4270-b60d-758a1a3369d6")
        page.wait_for_timeout(5000)
        
        # Check for elements that look like a watermark by text
        print("--- Text containing 'SHIT' or 'Journal' ---")
        matches = page.locator("*:text-matches('S.H.I.T|Journal', 'i')").all()
        for i, el in enumerate(matches):
            try:
                if el.is_visible():
                    tag = el.evaluate("el => el.tagName")
                    cls = el.get_attribute("class")
                    txt = el.text_content()[:50]
                    # Filter out common layout elements
                    if tag not in ["BODY", "HTML", "DIV"]: 
                         print(f"[{i}] Tag: {tag}, Class: {cls}, Text: {txt}")
            except:
                pass

        # Check for absolutely positioned elements overlaying the canvas
        print("\n--- Absolute Elements ---")
        absolute = page.evaluate("""
            () => {
                const results = [];
                const canvases = document.querySelectorAll('canvas');
                if (canvases.length === 0) return [];
                
                const canvasRect = canvases[0].getBoundingClientRect();
                
                document.querySelectorAll('*').forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (style.position === 'absolute' || style.position === 'fixed') {
                         const rect = el.getBoundingClientRect();
                         // Check if overlaps canvas
                         if (rect.left < canvasRect.right && rect.right > canvasRect.left &&
                             rect.top < canvasRect.bottom && rect.bottom > canvasRect.top) {
                                 results.push({
                                     tag: el.tagName,
                                     class: el.className,
                                     zIndex: style.zIndex,
                                     opacity: style.opacity,
                                     text: el.innerText.substring(0, 30)
                                 });
                         }
                    }
                });
                return results;
            }
        """)
        for item in absolute:
            print(item)
            
        browser.close()

if __name__ == "__main__":
    inspect_watermark_refined()
