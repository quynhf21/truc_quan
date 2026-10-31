"""Regression checks for the findings in UI_UX_AUDIT.md."""
import json
import re

from playwright.sync_api import sync_playwright
from audit_ui import BASE_URL, EDGE, OUT


def main():
    dash = json.loads((OUT / 'measurements.json').read_text(encoding='utf-8'))
    pages = json.loads((OUT / 'pages-measurements.json').read_text(encoding='utf-8'))
    for record in dash[:-1]:
        assert not record['errors'], record
        assert record['scrollWidth'] <= record['viewport'], record
        assert not record['clippedChartText'], record
        assert sum(link['current'] == 'page' for link in record['nav']) == 1
        assert all(label['htmlFor'] for label in record['labels'])
        assert record['reset'][0]['height'] >= 44
    for record in pages[1:]:
        assert record['scrollWidth'] <= record['viewport'], record
        assert not record['clippedChartText'], record
    assert pages[0]['history']['after_heading'] == 'Ai nên được ưu tiên?'
    assert dash[-1]['filter_test']['filtered'][0] == '14.654'
    assert dash[-1]['filter_test']['reset'][0] == '51.047'

    extra = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=EDGE, headless=True)
        page = browser.new_page()
        for width in [1440, 768, 375]:
            page.set_viewport_size({'width': width, 'height': 1000})
            page.goto(BASE_URL + '/risk', wait_until='networkidle')
            page.wait_for_selector('.js-plotly-plot')
            order = page.locator('.js-plotly-plot').first.evaluate('(e)=>e.calcdata[0].map(p=>p.x)')
            assert order == list(range(1, 11)), order
            extra.append({'width': width, 'deciles': order})
        page.goto(BASE_URL, wait_until='networkidle')
        for control_id, name in [
            ('tenure-filter', 'TENURE'), ('web-filter', 'WEB CAPABILITY'),
            ('value-filter', 'VALUE TIER'), ('risk-filter', 'RISK DECILE'),
        ]:
            button = page.get_by_role('button', name=re.compile(name))
            assert button.get_attribute('id') == control_id
            button.focus()
            button.press('Enter')
            assert button.get_attribute('aria-expanded') == 'true'
            button.press('Escape')
        # Measure note contrast against the actual white card background.
        color = page.locator('.kpi-note').first.evaluate('(e)=>getComputedStyle(e).color')
        rgb = [int(v)/255 for v in re.findall(r'\d+', color)[:3]]
        linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        ratio = 1.05/(sum(v*w for v, w in zip(linear, [.2126,.7152,.0722])) + .05)
        assert ratio >= 4.5, ratio
        extra.append({'keyboard_controls': 'PASS', 'note_contrast': ratio})
        browser.close()
    (OUT / 'regressions.json').write_text(json.dumps(extra, indent=2), encoding='utf-8')
    print('PASS: 12 Dash views, 9 Pages views, Back, decile 1–10, filter/reset, keyboard labels, note contrast')


if __name__ == '__main__':
    main()
