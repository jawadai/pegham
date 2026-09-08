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

    def _clean_stale_locks(self):
        """
        Removes stale Chromium singleton locks if the owning process is no longer running.
        Prevents 'Opening in existing browser session' crashes after restarts.
        """
        for lock_name in ["SingletonLock", "SingletonSocket", "SingletonCookie"]:
            lock_path = self.session_dir / lock_name
            if lock_path.exists() or lock_path.is_symlink():
                try:
                    lock_path.unlink()
                    logger.info(f"Cleaned stale Chromium lock: {lock_name}")
                except Exception as e:
                    logger.warning(f"Could not remove {lock_name}: {e}")

    async def initialize(self) -> bool:
        """
        Launches browser with persistent context and navigates to WhatsApp Web.
        Returns True if session is logged in, False if QR code needs scanning.
        """
        async with self._lock:
            if self.is_ready and self.page:
                return True

            self._clean_stale_locks()
            logger.info(f"🌐 Initializing WhatsApp Web service (session_dir={self.session_dir}, headless={self.headless})...")
            try:
                if not self.playwright:
                    self.playwright = await async_playwright().start()

                self.browser_context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_dir),
                    headless=self.headless,
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
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
                    "div[contenteditable='true']",
                    "button[aria-label='New chat']",
                    "header [data-icon='chat']",
                    "div[data-tab='3']"
                ]

                # Wait up to 45 seconds for session to restore from IndexedDB
                for _ in range(45):
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

    @staticmethod
    def _get_contact_search_variations(name: str) -> List[str]:
        """
        Generates smart search query variations for contact names.
        e.g. 'Youngerself' -> ['Youngerself', 'Younger self', 'Younger']
        e.g. 'Younger self' -> ['Younger self', 'Youngerself', 'Younger']
        """
        import re
        variations = [name.strip()]
        spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', name).strip()
        if spaced not in variations:
            variations.append(spaced)

        cleaned = name.strip()
        if " " not in cleaned:
            lower = cleaned.lower()
            for suffix in ["self", "khan", "bhai", "jan", "sb", "sahab"]:
                if lower.endswith(suffix) and len(lower) > len(suffix) + 2:
                    v_split = cleaned[:-len(suffix)].strip() + " " + cleaned[-len(suffix):].strip()
                    if v_split not in variations:
                        variations.append(v_split)
                    v_base = cleaned[:-len(suffix)].strip()
                    if v_base not in variations:
                        variations.append(v_base)
        else:
            no_space = cleaned.replace(" ", "").strip()
            if no_space not in variations:
                variations.append(no_space)
            first_word = cleaned.split()[0]
            if len(first_word) >= 3 and first_word not in variations:
                variations.append(first_word)

        return variations

    @staticmethod
    def _is_contact_match(target: str, candidate_text: str) -> bool:
        """
        Fuzzy & space-insensitive contact name matching.
        """
        import re
        t = target.strip().lower()
        c = candidate_text.strip().lower()
        if t in c or c in t:
            return True
        t_norm = re.sub(r'[^a-z0-9]', '', t)
        c_norm = re.sub(r'[^a-z0-9]', '', c)
        if t_norm and c_norm:
            if t_norm in c_norm or c_norm in t_norm:
                return True
            if len(t_norm) >= 4 and len(c_norm) >= 4 and t_norm[:4] == c_norm[:4]:
                return True
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
            # 0. Clean reset of previous search state or focus
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(0.2)
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(0.2)

            # Click cancel search / back button if active
            back_selectors = (
                "button[aria-label='Back'], "
                "button[aria-label='Cancel search'], "
                "button[aria-label='Clear search'], "
                "span[data-icon='back'], "
                "span[data-icon='x-alt'], "
                "#side button[aria-label='Back']"
            )
            cancel_btn = await self.page.query_selector(back_selectors)
            if cancel_btn:
                try:
                    await cancel_btn.click()
                    await asyncio.sleep(0.3)
                except Exception:
                    pass

            # 1. Locate and focus search box
            search_selectors = (
                "div[contenteditable='true'][data-tab='3'], "
                "div[aria-label='Search input text'], "
                "div[role='textbox'][title*='Search'], "
                "#side div[contenteditable='true'], "
                "button[aria-label='Search or start new chat']"
            )
            search_box = await self.page.query_selector(search_selectors)

            if search_box:
                await search_box.click()
                await asyncio.sleep(0.2)
            else:
                await self.page.keyboard.press("Control+Alt+/")
                await asyncio.sleep(0.3)

            # 2. Search for recipient using query variations
            search_variations = self._get_contact_search_variations(contact_name)
            chat_opened = False
            compose_box = None
            compose_selectors = (
                "#main footer div[contenteditable='true']",
                "#main div[data-lexical-editor='true']",
                "#main div[aria-label='Type a message']",
                "#main div[contenteditable='true'][data-tab='10']",
                "footer div[contenteditable='true']",
                "div[data-lexical-editor='true']"
            )

            for query_variant in search_variations:
                logger.info(f"🔎 Searching WhatsApp contact with query: '{query_variant}'...")

                # Clear search input
                if search_box:
                    try:
                        await search_box.click()
                        await asyncio.sleep(0.1)
                    except Exception:
                        pass
                try:
                    await self.page.evaluate("""() => {
                        const el = document.querySelector("div[contenteditable='true'][data-tab='3'], #side div[contenteditable='true']");
                        if (el) {
                            el.focus();
                            document.execCommand('selectAll', false, null);
                            document.execCommand('delete', false, null);
                        }
                    }""")
                except Exception:
                    pass
                await self.page.keyboard.press("Control+a")
                await self.page.keyboard.press("Backspace")
                await asyncio.sleep(0.2)

                # Type search query
                await self.page.keyboard.type(query_variant, delay=35)
                await asyncio.sleep(1.2)

                # Look for matching contact item in results
                chat_item = None
                items = await self.page.query_selector_all(
                    "#side div[role='listitem'], "
                    "#side div[role='row'], "
                    "div[data-testid='cell-frame-container'], "
                    "#pane-side div[role='listitem'], "
                    "div[aria-label='Search results.'] div[role='listitem']"
                )

                found_names = []
                for it in items[:10]:
                    try:
                        txt = await it.inner_text()
                        if txt:
                            first_line = txt.splitlines()[0].strip()
                            if first_line and first_line not in found_names:
                                found_names.append(first_line)
                    except Exception:
                        pass
                logger.info(f"Contacts/Chats found for '{query_variant}': {found_names}")

                for it in items[:8]:
                    txt = await it.inner_text()
                    if self._is_contact_match(contact_name, txt) or self._is_contact_match(query_variant, txt):
                        chat_item = it
                        logger.info(f"🎯 Matched contact item in WhatsApp: '{txt.splitlines()[0]}'")
                        break

                if chat_item:
                    await chat_item.click()
                    await asyncio.sleep(1.2)
                elif items:
                    # Click top search result item directly
                    try:
                        await items[0].click()
                        await asyncio.sleep(1.2)
                    except Exception:
                        await self.page.keyboard.press("ArrowDown")
                        await asyncio.sleep(0.3)
                        await self.page.keyboard.press("Enter")
                        await asyncio.sleep(1.0)

                # Check if compose box is now active
                try:
                    compose_box = await self.page.wait_for_selector(compose_selectors, timeout=4000)
                    if compose_box and await compose_box.is_visible():
                        chat_opened = True
                        break
                except Exception:
                    pass

            # Fallback: Try "New chat" address book drawer if main search didn't open chat
            if not chat_opened:
                logger.info(f"Main search did not open chat for '{contact_name}'. Trying 'New chat' address book drawer...")
                new_chat_btn = await self.page.query_selector("button[aria-label='New chat'], span[data-icon='chat'], #side header [data-icon='chat']")
                if new_chat_btn:
                    try:
                        await new_chat_btn.click()
                        await asyncio.sleep(0.8)

                        drawer_input = await self.page.query_selector("div[contenteditable='true'], div[aria-label='Search input text'], #side [contenteditable='true']")
                        if drawer_input:
                            await drawer_input.click()
                            await self.page.keyboard.type(contact_name, delay=35)
                            await asyncio.sleep(1.5)

                            drawer_items = await self.page.query_selector_all("#side div[role='listitem'], div[role='listitem']")
                            drawer_names = []
                            for it in drawer_items[:8]:
                                txt = await it.inner_text()
                                if txt:
                                    drawer_names.append(txt.splitlines()[0].strip())
                                if self._is_contact_match(contact_name, txt):
                                    logger.info(f"🎯 Matched contact in New Chat drawer: '{txt.splitlines()[0]}'")
                                    await it.click()
                                    await asyncio.sleep(1.2)
                                    break
                            else:
                                if drawer_items:
                                    logger.info(f"Clicking top result in New Chat drawer: '{drawer_names[0] if drawer_names else 'first'}'")
                                    await drawer_items[0].click()
                                    await asyncio.sleep(1.2)

                            compose_box = await self.page.wait_for_selector(compose_selectors, timeout=4000)
                            if compose_box and await compose_box.is_visible():
                                chat_opened = True
                    except Exception as e:
                        logger.warning(f"New chat drawer attempt failed: {e}")

            if not chat_opened or not compose_box or not await compose_box.is_visible():
                logger.warning(f"Could not open active chat for '{contact_name}' after trying variations {search_variations}.")
                await self.page.keyboard.press("Escape")
                return {
                    "success": False,
                    "contact": contact_name,
                    "message": message,
                    "error": f"WhatsApp par '{contact_name}' nahi mila."
                }

            # 3. Type message and send
            await compose_box.click()
            await asyncio.sleep(0.2)
            await self.page.keyboard.type(message, delay=20)
            await asyncio.sleep(0.3)
            await self.page.keyboard.press("Enter")
            await asyncio.sleep(1.0)

            # 4. Clean up state for subsequent requests
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(0.2)
            clean_btn = await self.page.query_selector(
                "button[aria-label='Cancel search'], "
                "button[aria-label='Clear search'], "
                "button[aria-label='Back'], "
                "span[data-icon='x-alt']"
            )
            if clean_btn:
                try:
                    await clean_btn.click()
                except Exception:
                    pass

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

