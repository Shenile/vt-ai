import os
import json
from playwright.sync_api import sync_playwright, TimeoutError

def capture_screenshot_and_dom(url, file_name, file_path):
    print(f"Ensuring directory exists: {file_path}")
    os.makedirs(file_path, exist_ok=True)

    try:
        with sync_playwright() as p:
            print("Launching Chromium browser in headless mode...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                device_scale_factor=1,
                is_mobile=False
            )
            page = context.new_page()
            print(f"Navigating to URL: {url}")
            page.goto(url, wait_until="networkidle", timeout=15000)

            page.add_style_tag(content="""
                * {
                    animation: none !important;
                    transition: none !important;
                }
            """)

            print("Waiting for fonts to be ready...")
            page.evaluate("() => new Promise(resolve => document.fonts.ready.then(resolve))")

            # Screenshot
            output_path = os.path.join(file_path, f"{file_name}.png")
            print(f"Saving screenshot to: {output_path}")
            page.screenshot(path=output_path, full_page=True)

            # DOM snapshot
            print("Extracting DOM snapshot...")
            dom_snapshot = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('*')).map(el => {
                    const rect = el.getBoundingClientRect();
                    return {
                        tag: el.tagName.toLowerCase(),
                        text: el.innerText,
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    };
                });
            }""")

            dom_path = os.path.join(file_path, f"{file_name}_dom.json")
            with open(dom_path, 'w') as f:
                json.dump(dom_snapshot, f, indent=2)

            print(f"DOM snapshot saved to: {dom_path}")
            print("✓ Screenshot + DOM capture completed.")

    except TimeoutError:
        print("TimeoutError: Page load timed out.")
    except Exception as e:
        print(f"Exception during capture: {e}")
