"""Read-only browser audit. Requires Playwright and an installed Microsoft Edge."""
import json
import os
from pathlib import Path
import re

from playwright.sync_api import sync_playwright

PROJECT = Path(__file__).resolve().parents[2]
OUT = PROJECT / "work" / "build" / os.environ.get("UI_AUDIT_DIR", "ui-audit")
BASE_URL = os.environ.get("DASH_AUDIT_URL", "http://127.0.0.1:8050")
OUT.mkdir(parents=True, exist_ok=True)
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

MEASURE = """
() => {
  const rect = e => {
    const r = e.getBoundingClientRect();
    return {x:r.x,y:r.y,width:r.width,height:r.height};
  };
  const shown = e => e.getBoundingClientRect().width > 0;
  return {
    viewport: innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
    title: document.querySelector('h1')?.textContent,
    nav: [...document.querySelectorAll('.nav-item,.nav')].map(e=>({
      text:e.textContent, cls:e.className, current:e.getAttribute('aria-current')
    })),
    reset: [...document.querySelectorAll('button')].filter(e=>/Đặt lại/.test(e.textContent)).map(e=>({
      text:e.textContent, ...rect(e), size:getComputedStyle(e).fontSize
    })),
    labels: [...document.querySelectorAll('label')].map(e=>({
      text:e.textContent, htmlFor:e.htmlFor, wrapsControl:!!e.querySelector('input,select')
    })),
    inputs: [...document.querySelectorAll('input')].map(e=>({
      id:e.id,role:e.getAttribute('role'), ariaLabel:e.getAttribute('aria-label'),
      labelledby:e.getAttribute('aria-labelledby')
    })),
    smallText: [...document.querySelectorAll('.kpi-note,.panel-note,.footer,.policy-detail small')]
      .slice(0,8).map(e=>({text:e.textContent.slice(0,70),size:getComputedStyle(e).fontSize,
        color:getComputedStyle(e).color,background:getComputedStyle(e).backgroundColor})),
    overflow: [...document.querySelectorAll('body *')].filter(shown).filter(e=>{
      const r=e.getBoundingClientRect();
      return r.right > innerWidth+2 && r.width > 5 && !e.closest('.modebar');
    }).slice(0,12).map(e=>({tag:e.tagName,cls:typeof e.className==='string'?e.className:'',
      text:e.textContent.slice(0,60),...rect(e)})),
    clippedChartText: [...document.querySelectorAll('.js-plotly-plot text')].filter(shown)
      .filter(e=>{
        const p=e.closest('.js-plotly-plot');
        const a=e.getBoundingClientRect(), b=p.getBoundingClientRect();
        return a.width>0 && (a.left<b.left-2 || a.right>b.right+2 || a.bottom>b.bottom+2);
      }).slice(0,15).map(e=>({text:e.textContent,...rect(e)}))
  };
}
"""


def run():
    records = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=EDGE, headless=True)
        for width, height in [(1440, 1000), (768, 1024), (375, 812)]:
            page = browser.new_page(viewport={"width": width, "height": height})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            for route in ["", "drivers", "risk", "strategy"]:
                page.goto(f"{BASE_URL}/{route}", wait_until="networkidle")
                page.wait_for_selector("#page-content h1", timeout=30000)
                page.screenshot(path=str(OUT / f"dash-{route or 'overview'}-{width}.png"), full_page=True)
                record = page.evaluate(MEASURE)
                record.update(route=route or "overview", errors=list(errors))
                if route == 'risk':
                    record['decileOrder'] = page.locator('.js-plotly-plot').first.evaluate('(e)=>e.calcdata[0].map(p=>p.x)')
                records.append(record)
                print(width, route or "overview", "overflow=", record["scrollWidth"]-width,
                      "clipped=", len(record["clippedChartText"]), flush=True)
            page.close()
        (OUT / "measurements.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.goto(f"{BASE_URL}/", wait_until="networkidle")
        # Open tenure filter, select a real option, then verify reset from UI.
        page.locator("#tenure-filter").click()
        page.screenshot(path=str(OUT / "dash-dropdown-open.png"), full_page=False)
        page.get_by_text("12–18 tháng", exact=True).first.click()
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT / "dash-filtered.png"), full_page=False)
        filtered_values = page.locator(".kpi-value").all_text_contents()
        page.get_by_role("button", name=re.compile("Đặt lại")).click()
        page.wait_for_timeout(800)
        reset_values = page.locator(".kpi-value").all_text_contents()
        records.append({"filter_test": {"filtered": filtered_values, "reset": reset_values}})
        page.close()
        browser.close()
    (OUT / "measurements.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    run()
