"""
WhatsApp Web Automation Service using Playwright.
Maintains persistent session state without requiring the official Meta Cloud API.
"""

import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path
from playwright.async_api import async_playwright, Playwright, BrowserContext, Page
from backend.config import settings
from backend.utils.logger import logger


class WhatsAppService:
    """
    Manages a persistent Playwright browser context to interact with WhatsApp Web.
    """

    def __init__(self, session_dir: Optional[str] = None, headless: Optional[bool] = None):
        self.session_dir = Path(session_dir or settings.WHATSAPP_SESSION_DIR)
        self.headless = settings.WHATSAPP_HEADLESS if headless is None else headless
        self.playwright: Optional[Playwright] = None
        self.browser_context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_ready: bool = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> bool:
        """
        Launches browser with persistent context and navigates to WhatsApp Web.
        Returns True if session is logged in, False if QR code needs scanning.
        """
        async with self._lock:
            if self.is_ready and self.page:
                return True

            logger.info(f"🌐 Initializing WhatsApp Web service (session_dir={self.session_dir}, headless={self.headless})...")
            try:
                if not self.playwright:
                    self.playwright = await async_playwright().start()

                self.browser_context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_dir),
                    headless=self.headless,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-blink-features=AutomationControlled",
                    ],
                    viewport={"width": 1280, "height": 800}
                )

                self.page = self.browser_context.pages[0] if self.browser_context.pages else await self.browser_context.new_page()
                logger.info("Loading https://web.whatsapp.com...")
                await self.page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

                # Check if session is logged in by polling for key landmarks
                logged_in_selectors = [
                    "#pane-side",
                    "#side",
                    "div[aria-label='Chat list']",
                    "div[role='grid']",
                    "button[aria-label='New chat']"
                ]

                # Wait up to 25 seconds for session to restore from IndexedDB
                for _ in range(25):
                    for selector in logged_in_selectors:
                        try:
                            el = await self.page.query_selector(selector)
                            if el and await el.is_visible():
                                self.is_ready = True
                                logger.info(f"✅ WhatsApp Web authenticated & ready! (Found element: '{selector}')")
                                return True
                        except Exception:
                            pass
                    await asyncio.sleep(1)

                logger.warning("⚠️ WhatsApp Web is not logged in. Run 'python scripts/setup_whatsapp.py' to pair device.")
                self.is_ready = False
                return False

            except Exception as e:
                logger.error(f"Failed to initialize WhatsApp Web service: {e}")
                self.is_ready = False
                return False

    async def send_message(self, contact_name: str, message: str) -> Dict[str, Any]:
        """
        Searches for a contact/chat in WhatsApp Web and sends a message.
        """
        if not self.is_ready or not self.page:
            ready = await self.initialize()
            if not ready:
                return {
                    "success": False,
                    "contact": contact_name,
                    "message": message,
                    "error": "WhatsApp is not logged in. Run 'python scripts/setup_whatsapp.py' to link device."
                }

        logger.info(f"📨 Attempting to send WhatsApp message to '{contact_name}': \"{message}\"")
        try:
            # 1. Focus search box
            search_box = await self.page.query_selector(
                "div[contenteditable='true'][data-tab='3'], div[aria-label='Search input text'], div[role='textbox'][title*='Search'], #side div[contenteditable='true']"
            )

            if not search_box:
                # Try keyboard shortcut to focus search
                await self.page.keyboard.press("Control+Alt+/")
                await asyncio.sleep(0.5)
            else:
                await search_box.click()
                await asyncio.sleep(0.3)

            # Clear existing search query
            await self.page.keyboard.press("Control+A")
            await self.page.keyboard.press("Backspace")
            await asyncio.sleep(0.2)

            # Type contact name
            await self.page.keyboard.type(contact_name, delay=40)
            await asyncio.sleep(1.5)

            # Look for contact item in results
            contact_matched = False
            chat_items = await self.page.query_selector_all("#pane-side span[title]")
            for item in chat_items:
                title = await item.get_attribute("title")
                if title and contact_name.lower() in title.lower():
                    await item.click()
                    contact_matched = True
                    break

            if not contact_matched:
                # Press enter to open top matched search result
                await self.page.keyboard.press("Enter")
                await asyncio.sleep(1.0)

            # 2. Wait for message compose input box to appear in active chat
            compose_box_selectors = [
                "#main footer div[contenteditable='true']",
                "footer div[contenteditable='true'][data-tab='10']",
                "div[contenteditable='true'][data-tab='10']",
                "footer div[contenteditable='true']",
                "div[aria-label='Type a message']"
            ]

            compose_box = None
            for selector in compose_box_selectors:
                try:
                    compose_box = await self.page.wait_for_selector(selector, timeout=5000)
                    if compose_box and await compose_box.is_visible():
                        break
                except Exception:
                    continue

            if not compose_box:
                return {
                    "success": False,
                    "contact": contact_name,
                    "message": message,
                    "error": f"Could not find or open chat for '{contact_name}'."
                }

            # 3. Type message and send
            await compose_box.click()
            await asyncio.sleep(0.3)
            await self.page.keyboard.type(message, delay=25)
            await asyncio.sleep(0.4)
            await self.page.keyboard.press("Enter")
            await asyncio.sleep(1.0)

            logger.info(f"🎉 Successfully sent WhatsApp message to '{contact_name}'!")
            return {
                "success": True,
                "contact": contact_name,
                "message": message,
                "status": "Sent"
            }

        except Exception as e:
            logger.error(f"Error sending WhatsApp message to '{contact_name}': {e}")
            return {
                "success": False,
                "contact": contact_name,
                "message": message,
                "error": str(e)
            }

    async def get_unread_messages(self) -> List[Dict[str, Any]]:
        """
        Scans WhatsApp Web chat list for unread message badges.
        """
        if not self.is_ready or not self.page:
            ready = await self.initialize()
            if not ready:
                return []

        logger.info("🔍 Scanning for unread WhatsApp messages...")
        unread_chats = []
        try:
            # Query all unread badges in the side pane
            badge_elements = await self.page.query_selector_all(
                "#pane-side span[aria-label*='unread message'], #pane-side span[aria-label*='Unread message']"
            )

            for badge in badge_elements:
                try:
                    badge_text = await badge.inner_text()
                    chat_row = await badge.evaluate_handle("el => el.closest('[role=\"listitem\"], [role=\"row\"]')")
                    if chat_row:
                        title_el = await chat_row.as_element().query_selector("span[title]")
                        sender = await title_el.get_attribute("title") if title_el else "Unknown"
                        unread_chats.append({
                            "sender": sender,
                            "unread_count": badge_text,
                        })
                except Exception:
                    pass

            logger.info(f"Found {len(unread_chats)} unread conversations.")
            return unread_chats

        except Exception as e:
            logger.error(f"Error reading unread messages: {e}")
            return []

    async def close(self):
        """
        Closes browser context cleanly.
        """
        if self.browser_context:
            logger.info("Closing WhatsApp browser context...")
            try:
                await self.browser_context.close()
            except Exception:
                pass
            self.browser_context = None
            self.page = None
            self.is_ready = False

        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception:
                pass
            self.playwright = None


# Global service instance
whatsapp_service = WhatsAppService()

