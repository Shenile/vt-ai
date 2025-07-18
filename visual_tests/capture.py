import os
import json
from dataclasses import dataclass
from typing import Dict, List, Optional
from playwright.sync_api import sync_playwright, TimeoutError
from config import TEST_URLS
from git_utils import is_ui_only_commit
#dummy
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

@dataclass
class CaptureResult:
    screenshot_path: str
    dom_path: str
    success: bool
    error: Optional[str] = None

class PageCapturer:
    """Handles screenshot and DOM capture for web pages."""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.viewport = {"width": 1280, "height": 800}
        self.timeout = 15000
        
    def _prepare_environment(self, page) -> None:
        """Remove animations and wait for fonts to load."""
        page.add_style_tag(content="""
            * {
                animation: none !important;
                transition: none !important;
            }
        """)
        page.evaluate("() => new Promise(resolve => document.fonts.ready.then(resolve))")

    def _capture_dom(self, page) -> List[Dict]:
        """Enhanced DOM snapshot with visual and structural information."""
        return page.evaluate("""() => {
            const elements = [];
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_ELEMENT,
                null,
                false
            );

            while (walker.nextNode()) {
                const el = walker.currentNode;
                const rect = el.getBoundingClientRect();
                
                if (rect.width > 0 && rect.height > 0) {
                    elements.push({
                        tag: el.tagName.toLowerCase(),
                        text: (el.innerText || "").trim().replace(/\\s+/g, " "),
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height),
                        parent_id: el.parentElement?.id || null,
                        is_visible: window.getComputedStyle(el).display !== 'none',
                        is_clickable: el.hasAttribute('onclick') || 
                                     ['button','a','input'].includes(el.tagName.toLowerCase())
                    });
                }
            }
            return elements;
        }""")

    def capture(self, url: str, name: str) -> CaptureResult:
        """Capture screenshot and DOM for a given URL."""
        os.makedirs(self.output_dir, exist_ok=True)
        screenshot_path = os.path.join(self.output_dir, f"{name}.png")
        dom_path = os.path.join(self.output_dir, f"{name}_dom.json")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport=self.viewport,
                    device_scale_factor=1,
                    is_mobile=False
                )
                page = context.new_page()
                
                page.goto(url, wait_until="networkidle", timeout=self.timeout)
                self._prepare_environment(page)
                
                page.screenshot(path=screenshot_path, full_page=True)
                dom_snapshot = self._capture_dom(page)
                
                with open(dom_path, 'w') as f:
                    json.dump(dom_snapshot, f, indent=2)
                    
                return CaptureResult(
                    screenshot_path=screenshot_path,
                    dom_path=dom_path,
                    success=True
                )
                
        except TimeoutError:
            error = f"Timeout after {self.timeout}ms loading {url}"
        except Exception as e:
            error = f"Error capturing {url}: {str(e)}"
            
        return CaptureResult(
            screenshot_path="",
            dom_path="",
            success=False,
            error=error
        )

def save_page_snapshots(commit_hash: str) -> Optional[Dict[str, CaptureResult]]:
    """Save snapshots for all test URLs if UI changes exist."""
    if not is_ui_only_commit(commit_hash):
        print(f"Skipping non-UI commit: {commit_hash}")
        return None
    
    baseline_dir = os.path.join(CURRENT_DIR, 'baseline', commit_hash)
    capturer = PageCapturer(baseline_dir)
    results = {}

    for name, url in TEST_URLS.items():
        print(f"Capturing {name} ({url})...")
        result = capturer.capture(url, name)
        
        if result.success:
            print(f"✓ Saved to {result.screenshot_path}")
        else:
            print(f"✗ Failed: {result.error}")
            
        results[name] = result

    return results