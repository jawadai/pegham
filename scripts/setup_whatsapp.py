#!/usr/bin/env python3
"""
WhatsApp Web One-Time QR Setup Script.
Launches a visible browser window to scan the WhatsApp Web QR code once.
Session tokens and cookies are persisted in ./whatsapp_session for future headless use.
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# Add repository root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.config import settings
from backend.utils.logger import logger


async def setup_whatsapp_session():
    session_dir = settings.session_path
    logger.info(f"Opening WhatsApp Web for initial QR code login...")
    logger.info(f"Session directory: {session_dir.resolve()}")
    logger.info("👉 Scan the QR code with your phone (WhatsApp -> Linked Devices -> Link a Device).")

    async with async_playwright() as p:
        # Launch visible browser with persistent context
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
            viewport={"width": 1280, "height": 800}
        )

        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

        logger.info("Waiting for WhatsApp Web to load...")
        logger.info("👉 Please scan the QR code in the browser with your phone.")
        logger.info("   (WhatsApp -> Settings / Menu -> Linked Devices -> Link a Device)")

        # Multiple resilient selectors representing a logged-in WhatsApp Web state
        logged_in_selectors = [
            "#pane-side",
            "#side",
            "div[aria-label='Chat list']",
            "div[role='grid']",
            "div[contenteditable='true']",
            "button[aria-label='New chat']",
            "header [data-icon='chat']",
            "div[data-tab='3']",
        ]

        start_time = asyncio.get_event_loop().time()
        timeout_seconds = 180  # 3 minutes
        logged_in = False
        last_logged_time = 0

        while asyncio.get_event_loop().time() - start_time < timeout_seconds:
            elapsed = int(asyncio.get_event_loop().time() - start_time)
            
            # Check if any logged in element has appeared
            for selector in logged_in_selectors:
                try:
                    el = await page.query_selector(selector)
                    if el and await el.is_visible():
                        logged_in = True
                        logger.info(f"Detected WhatsApp Web interface element: '{selector}'")
                        break
                except Exception:
                    pass

            if logged_in:
                break

            # Periodic status log every 15 seconds
            if elapsed - last_logged_time >= 15:
                logger.info(f"⏳ Waiting for QR scan and chat sync... ({elapsed}s / {timeout_seconds}s)")
                last_logged_time = elapsed

            await asyncio.sleep(2)

        if logged_in:
            logger.info("🎉 SUCCESS: WhatsApp Web is logged in! Session successfully saved.")
            logger.info("Writing session cookies & IndexedDB to disk...")
            await asyncio.sleep(4)
            logger.info("Done! You will NOT need to scan the QR code again.")
        else:
            logger.error("Login timed out after 3 minutes. Please ensure your phone is connected to the internet and re-run.")

    await context.close()


if __name__ == "__main__":
    asyncio.run(setup_whatsapp_session())
