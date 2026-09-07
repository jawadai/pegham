#!/usr/bin/env python3
"""
Test script to verify sending a message using the persisted WhatsApp session.
"""

import asyncio
import sys
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.services.whatsapp import whatsapp_service
from backend.utils.logger import logger


async def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/test_whatsapp.py <contact_name> <message>")
        print("Example: python scripts/test_whatsapp.py 'Hamza' 'Testing Kabootar AI!'")
        return

    contact = sys.argv[1]
    message = " ".join(sys.argv[2:])

    logger.info(f"Testing WhatsApp message delivery to: {contact}")
    await whatsapp_service.initialize()
    result = await whatsapp_service.send_message(contact, message)
    logger.info(f"Result: {result}")
    await whatsapp_service.close()


if __name__ == "__main__":
    asyncio.run(main())
