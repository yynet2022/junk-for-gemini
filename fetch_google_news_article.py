import asyncio
from pyppeteer import launch
from pyppeteer.browser import Browser
from pyppeteer.page import Page
from pyppeteer.errors import TimeoutError
import time

async def main():
    browser: Browser = await launch(
        headless=False,
        executablePath='c:/Program Files/Google/Chrome/Application/chrome.exe',
    )
    page: Page = await browser.newPage()
    url = "https://news.google.com/rss/articles/CBMibEFVX3lxTE1jbHhEQkhsblc5SFBqUUJkV3QwbElLdkdiT1dyaFdDV2tZRG1MNHJieS10Y2tMVExaRkp6a04yWEFtbG9EYlJmM2NWb2oxNTB5OGtSb2IyZWEzeXdhTlB4V0JSLVBVanZ4RXFobw?oc=5"

    try:
        # 1. 最初のページへの遷移を開始させる（読み込み完了は待たない）
        #    NetworkErrorを回避するため、ここでは完了を待たないのがポイント
        await page.goto(url, {'waitUntil': 'domcontentloaded'})

        # 2. JavaScriptによるリダイレクトが完了し、かつ、
        #    遷移後のページのネットワークが落ち着くまで待つ (これが核心)
        #    networkidle0は厳しすぎるのでnetworkidle2を使う
        print("Waiting for the page to stabilize after redirect...")
        await page.waitForNavigation({'waitUntil': 'networkidle2'})
        print("Page has stabilized.")

    except TimeoutError as e:
        print(f"Timeout: {e}")
        print("Timeout occurred, continuing process...")
        pass

    """
    time.sleep(10)
    text = plainText()
    content = await page.content()
    """

    print(f"Final URL: {page.url}")
    await page.screenshot({"path": "./a.png"})
    time.sleep(3)
    await page.screenshot({"path": "./b.png"})
    await browser.close()

if __name__ == "__main__":
    asyncio.new_event_loop().run_until_complete(main())
