import asyncio
import os
import uvicorn
from twitch_chat_service.server import create_app


app = create_app()
