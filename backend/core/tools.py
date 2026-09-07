"""
Tool schemas and execution handlers for LLM function calling in Pipecat.
"""

from typing import Dict, Any
from backend.services.whatsapp import whatsapp_service
from backend.utils.logger import logger

# JSON Schema definitions for OpenAI / Groq / Anthropic function calling
WHATSAPP_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "send_whatsapp_message",
            "description": "Sends a WhatsApp text message to a specific contact or group name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "contact_name": {
                        "type": "string",
                        "description": "The exact or partial name of the contact or group as saved in WhatsApp (e.g. 'Ali', 'Hamza Khan', 'Office Group')."
                    },
                    "message": {
                        "type": "string",
                        "description": "The text content of the message to send."
                    }
                },
                "required": ["contact_name", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_unread_messages",
            "description": "Scans WhatsApp Web for unread messages and returns the sender names and recent snippets.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


async def handle_tool_call(function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dispatches tool calls to the appropriate underlying service.
    """
    logger.info(f"Executing tool call: {function_name} with args: {arguments}")

    if function_name == "send_whatsapp_message":
        contact = arguments.get("contact_name", "")
        message = arguments.get("message", "")
        result = await whatsapp_service.send_message(contact_name=contact, message=message)
        return result

    elif function_name == "check_unread_messages":
        unread = await whatsapp_service.get_unread_messages()
        return {"unread_messages": unread}

    logger.warning(f"Unknown tool call: {function_name}")
    return {"error": f"Function {function_name} not recognized"}
