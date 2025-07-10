import os
from playwright.sync_api import sync_playwright, TimeoutError

def capture_screenshot(url, file_name, file_path):
    # Ensure output directory exists
    os.makedirs(file_path, exist_ok=True)

    try:
        with sync_playwright() as p:
            with p.chromium.launch(headless=True) as browser:
                context = browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    device_scale_factor=1,
                    is_mobile=False
                )
                page = context.new_page()

                # Go to the target URL and wait until the network is idle
                page.goto(url, wait_until="networkidle", timeout=15000)

                # Disable CSS animations and transitions
                page.add_style_tag(content="""
                    * {
                        animation: none !important;
                        transition: none !important;
                    }
                """)

                # Wait for fonts to finish loading
                page.evaluate("return document.fonts.ready")

                # Capture a full-page screenshot
                output_path = os.path.join(file_path, f"{file_name}.png")
                page.screenshot(path=output_path, full_page=True)

                print(f"Screenshot saved to: {output_path}")

    except TimeoutError:
        print("Timeout occurred while waiting for page or selector.")
    except Exception as e:
        print(f"Error during screenshot capture: {e}")
