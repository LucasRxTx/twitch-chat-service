import asyncio
print("here")
from twitch_chat_analytics_service.analytics import handle_message_stream


asyncio.run(handle_message_stream())