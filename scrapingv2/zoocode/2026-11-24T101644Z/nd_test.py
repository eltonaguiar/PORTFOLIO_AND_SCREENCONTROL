import asyncio, time

async def main():
    import nodriver as uc
    t = time.time()
    browser = await uc.start(headless=True, browser_args=["--no-sandbox"])
    try:
        page = await browser.get("https://www.g2.com/")
        await asyncio.sleep(6)
        title = await page.evaluate("document.title")
        wd = await page.evaluate("navigator.webdriver")
        text = await page.evaluate("document.body ? document.body.innerText.slice(0,180) : ''")
        print(f"RESULT nodriver title={title[:45]!r} webdriver={wd} {time.time()-t:.1f}s")
        print("RESULT text:", repr(text[:150]))
    except Exception as e:
        print("RESULT FAIL", type(e).__name__, str(e)[:120])
    finally:
        try: browser.stop()
        except Exception: pass

try:
    asyncio.run(main())
except Exception as e:
    print("LOOP", type(e).__name__, str(e)[:80])
