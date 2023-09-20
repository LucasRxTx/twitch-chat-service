import datetime
import json
import logging
from emoji import demojize
from typing import Sequence, Union
from textblob import TextBlob
from twitch_chat_models.models import database, redis, messages


logger = logging.getLogger(__name__)


def average(values: Sequence[float]) -> float:
    """Average values from an iterable of floats."""
    return sum(values) / len(values)


def emoji_from_score(score: float) -> str:
    """Represent a float between 1.0 and -1.0 as an emoji."""
    # TODO: tweek logic
    emoji = "\U0001F642"
    if score > -0.9:
        emoji = "\U0001F92C"
    if score > -0.5:
        emoji = "\U0001F621"
    if score > -0.3:
        emoji = "\U0001F620"
    if score > -0.2:
        emoji = "\U0001F612"
    if score >= -0.1 and score < 0.05:
        emoji = "\U0001F610"
    if score >= 0.05:
        emoji = "\U0001F642"
    if score > 0.2:
        emoji = "\U0001F60A"
    if score > 0.3:
        emoji = "\U0001F604"
    if score > 0.7:
        emoji = "\U0001F606"

    return emoji


def analyze_sentiment(msg: str) -> float:
    """Perform basic sentiment analysis on any text."""
    blob = TextBlob(msg)
    scores = [sentence.polarity for sentence in blob.sentences]
    return average(scores)


async def handle_twitch_message_create(message: dict):
    try:
        logger.info(message["data"])
        data: dict = json.loads(message["data"].decode("utf-8"))
    except Exception as e:
        logger.exception("Error creating twitch message.")
        return None

    data["created_at"] = datetime.datetime.fromisoformat(data["created_at"])
    sentiment: float = analyze_sentiment(msg=data["body"])
    data["body"] = demojize(data["body"])
    data["sentiment"] = sentiment
    data["sentiment_emoji"] = demojize(emoji_from_score(sentiment))
    body_lower = data["body"].lower()
    data["has_lul"] = "lul" in body_lower or "lol" in body_lower

    query = messages.insert()
    await database.execute(query=query, values=data)


async def handle_message_stream():
    p = redis.pubsub()
    await p.subscribe("TwitchMessageCreated")
    await database.connect()
    try:
        while True:
            message: Union[int, dict] = await p.get_message()
            if isinstance(message, dict):
                await handle_twitch_message_create(message)
    except KeyboardInterrupt:
        await database.disconnect()
        exit()
