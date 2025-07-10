def capture_screenshot(url, file_name, file_path):
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

                page.goto(url, wait_until="networkidle", timeout=15000)

                page.add_style_tag(content="""
                    * {
                        animation: none !important;
                        transition: none !important;
                    }
                """)

                # ✅ Properly wait for fonts to load
                page.evaluate("() => new Promise(resolve => document.fonts.ready.then(resolve))")

                output_path = os.path.join(file_path, f"{file_name}.png")
                page.screenshot(path=output_path, full_page=True)

                print(f"Screenshot saved to: {output_path}")

    except TimeoutError:
        print("Timeout occurred while waiting for page or selector.")
    except Exception as e:
        print(f"Error during screenshot capture: {e}")
