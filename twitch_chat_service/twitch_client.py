import asyncio
import re
import datetime
from typing import Dict, Any, AsyncGenerator, Optional


class TwitchIRCClient:
    server = 'irc.chat.twitch.tv'
    port = 6667
    # For parsing data out of raw string from IRC.
    re_string = r"^\:(?P<nickname>[a-zA-Z0-9]*)!.*\:(?P<message>.*)$"
    message_re = re.compile(re_string)

    def __init__(self, nickname: str, token: str, max_buffer: int = 100):
        self.nickname = nickname.lower()  # Twitch calls this nickname
        self.token = token  # oauth2 token from Twitch
        self.max_buffer = max_buffer

        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

    async def handle_message(self, msg: str, writer):
        """ Basic message handler.

        Will pong on ping to keep connection alive.
        """
        if "PING" in msg:
            print("< PONG")
            if self.writer is not None:
                self.writer.write("PONG :tmi.twitch.tv".encode("utf-8"))
        elif "MSG" in msg:
            match = self.message_re.match(msg)
            if match:
                data = dict(
                    nickname=match.group(1).strip().lower(),
                    body=match.group(2).strip(),
                    created_at=datetime.datetime.now(datetime.timezone.utc)
                )
                return data

    async def stream(
            self,
            channel: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        channel = channel.lower()
        print(self.nickname, self.token, channel)
        self.reader, self.writer = await asyncio.open_connection(
            self.server,
            self.port
        )

        self.writer.write(f"PASS oauth:{self.token}\n".encode("utf-8"))
        self.writer.write(f"NICK {self.nickname}\n".encode("utf-8"))
        self.writer.write(f"JOIN #{channel}\n".encode("utf-8"))
        await self.writer.drain()

        try:
            while True:
                msg: bytes = await self.reader.read(self.max_buffer)
                data: Dict[str, Any] = \
                    await self.handle_message(msg.decode("utf-8"), channel)

                if data:
                    yield data
        except KeyboardInterrupt:
            self.writer.close()
            exit()
        finally:
            self.writer.close()
