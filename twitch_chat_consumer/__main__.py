import asyncio
import os
from twitch_chat_consumer.analytics import handle_message_stream
from twitch_chat_models.models import ensure_db_connection

ensure_db_connection()
asyncio.run(handle_message_stream())
