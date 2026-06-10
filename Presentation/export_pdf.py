"""
Export methodology_presentation.html → methodology_presentation.pdf
Uses Playwright (already installed) to screenshot each slide, PIL to combine.
"""
import asyncio
import os
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright

HTML_PATH = Path(__file__).parent / "methodology_presentation.html"
OUT_PDF   = Path(__file__).parent / "methodology_presentation.pdf"
SLIDES    = 16
WIDTH     = 1920
HEIGHT    = 1080


async def main():
    print(f"Opening {HTML_PATH} ...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page    = await browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
        await page.goto(HTML_PATH.as_uri(), wait_until="networkidle")

        images = []
        for i in range(1, SLIDES + 1):
            print(f"  Slide {i}/{SLIDES} ...", end=" ", flush=True)
            # call the JS show() function directly
            await page.evaluate(f"show({i})")
            # give Chart.js and fonts a moment to render
            await page.wait_for_timeout(350)
            buf = await page.screenshot(full_page=False, type="png")
            from io import BytesIO
            img = Image.open(BytesIO(buf)).convert("RGB")
            images.append(img)
            print("ok")

        await browser.close()

    print(f"\nSaving PDF to {OUT_PDF} ...")
    images[0].save(
        OUT_PDF,
        save_all=True,
        append_images=images[1:],
        resolution=150,
    )
    size_kb = OUT_PDF.stat().st_size // 1024
    print(f"Done!  {OUT_PDF.name}  ({size_kb} KB, {SLIDES} pages)")


asyncio.run(main())
