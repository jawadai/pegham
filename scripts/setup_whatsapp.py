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
        await page.goto("https://web.whatsapp.com", wait_until="networkidle")

        logger.info("Waiting for WhatsApp Web to load chats after QR scan...")
        
        # Selector for the main chat list search box or side panel
        chat_list_selector = "div[contenteditable='true'][data-tab='3']"
        
        try:
            # Wait up to 120 seconds for the user to scan the QR code
            await page.wait_for_selector(chat_list_selector, timeout=120000)
            logger.info("🎉 SUCCESS: WhatsApp Web is logged in! Session successfully saved.")
            logger.info("You will NOT need to scan the QR code again.")
            await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Login timed out or failed: {e}")
        finally:
            await context.close()


if __name__ == "__main__":
    asyncio.run(setup_whatsapp_session())
