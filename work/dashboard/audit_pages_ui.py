"""Check static Pages UI and browser history using an ephemeral local server."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Thread

from playwright.sync_api import sync_playwright
from audit_ui import EDGE, MEASURE, OUT, PROJECT


def run():
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        partial(SimpleHTTPRequestHandler, directory=str(PROJECT / "site")),
    )
    Thread(target=server.serve_forever, daemon=True).start()
    records = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=EDGE, headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            url = f"http://127.0.0.1:{server.server_port}/"
            page.goto(url, wait_until="networkidle")
            page.wait_for_selector("h1")
            for name in ["drivers", "risk", "strategy"]:
                page.locator(f'[data-page="{name}"]').click()
                page.wait_for_timeout(300)
            before = page.locator("h1").inner_text()
            page.go_back(wait_until="domcontentloaded")
            page.wait_for_timeout(300)
            history = {
                "before": before,
                "after_url": page.url,
                "after_heading": page.locator("h1").inner_text(),
                "active": page.locator(".nav.active").inner_text(),
            }
            records.append({"history": history})
            assert history['after_heading'] == 'Ai nên được ưu tiên?'
            page.go_forward(wait_until='domcontentloaded')
            page.wait_for_timeout(300)
            history['forward_heading'] = page.locator('h1').inner_text()
            assert history['forward_heading'] == before
            for width in [1440, 768, 375]:
                page.set_viewport_size({"width": width, "height": 1000})
                for name in ["overview", "risk", "strategy"]:
                    page.locator(f'[data-page="{name}"]').click()
                    page.wait_for_timeout(400)
                    page.screenshot(path=str(OUT / f"pages-{name}-{width}.png"), full_page=True)
                    record = page.evaluate(MEASURE)
                    record.update(page=name, variant="pages")
                    records.append(record)
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    (OUT / "pages-measurements.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    print(json.dumps(history, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run()
