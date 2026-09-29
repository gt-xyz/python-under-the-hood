"""Walk every lesson section in a headless browser at desktop and phone sizes.

    pip install playwright && python -m playwright install chromium
    python3 scripts/serve.py &          # in another terminal
    python3 tests/walkthrough.py        # add --no-python to skip the runnable boxes

Checks: no script errors; every prediction blurs its answer and reveals it; no sideways
scrolling at phone width; runnable examples produce output and a live bytecode stepper that
steps (desktop pass only).
"""
import sys
from playwright.sync_api import sync_playwright

URL = "http://localhost:8000/"
RUN_PYTHON = "--no-python" not in sys.argv
problems = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    for name, ctx_args in [("desktop", {"viewport": {"width": 1280, "height": 900}}),
                           ("iPhone 13", p.devices["iPhone 13"])]:
        page = browser.new_context(**ctx_args).new_page()
        page.on("pageerror", lambda e, n=name: problems.append(f"{n}: script error: {e}"))
        page.goto(URL)
        page.wait_for_timeout(300)
        width = page.evaluate("innerWidth")
        for l in range(page.evaluate("LESSONS.length")):
            for s in range(page.evaluate(f"LESSONS[{l}].steps.length")):
                where = f"{name} lesson {l + 1} section {s + 1}"
                page.evaluate(f"go({l}, {s}, false)")
                page.wait_for_timeout(60)
                if page.locator(".predict").count():
                    if page.locator(".veiled").count() == 0 and page.locator(".reveal .ans").count():
                        problems.append(f"{where}: answer not blurred before predicting")
                    page.locator(".veil").first.click()
                    if page.locator(".veiled").count() or page.locator(".veil").count():
                        problems.append(f"{where}: answer still blurred after tapping Show answer")
                for sel in ["[data-act=next]", "[data-a=n]"]:
                    if page.locator(sel).count():
                        page.locator(sel).first.click()
                if RUN_PYTHON and name == "desktop" and page.locator(".try-run").count():
                    page.locator(".try-run").first.click()
                    page.locator(".try-out > *").first.wait_for(timeout=90000)
                    text = page.inner_text(".try-out")
                    if "couldn't start" in text:
                        problems.append(f"{where}: {text[:120]}")
                    elif "internal" in text:
                        problems.append(f"{where}: tracer problem: {text[:160]}")
                    elif page.locator(".try-out .live").count() == 0:
                        problems.append(f"{where}: no bytecode view after running")
                    live = page.locator(".try-out .st [data-act=next]")
                    if live.count():
                        before = page.inner_text(".try-out .note-slot")
                        live.first.click()
                        if page.inner_text(".try-out .note-slot") == before:
                            problems.append(f"{where}: live stepper did not step")
                if page.evaluate("document.documentElement.scrollWidth") > width:
                    problems.append(f"{where}: page scrolls sideways")
        print(f"{name}: done")
    browser.close()

print("\n".join(problems) if problems else "All sections passed.")
sys.exit(1 if problems else 0)
