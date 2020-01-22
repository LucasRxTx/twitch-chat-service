import json
from emoji import emojize
from ariadne import (
    QueryType,
    make_executable_schema,
    load_schema_from_path,
    SubscriptionType
)
from typing import List, AsyncGenerator, Dict, Any, Mapping
from twitch_chat_models.models import (
    database,
    messages,
    redis,
    channel_metrics_query
)
from twitch_chat_service.twitch_client import TwitchIRCClient
from twitch_chat_analytics_service.analytics import emoji_from_score


type_defs = load_schema_from_path("twitch_chat_service/graphql/types.graphql")
query = QueryType()
subscription = SubscriptionType()

#
# GraphQL Resolvers
#
@query.field("messages")
async def resolve_messages(_, info) -> List[Dict[str, Any]]:
    query = messages.select()
    results = await database.fetch_all(query)
    data: List[dict] = [
        dict(
            id=result["id"],
            nickname=result["nickname"],
            body=emojize(result["body"]),
            sentiment=result["sentiment"],
            created_at=str(result["created_at"]),
            sentiment_emoji=emojize(result["sentiment_emoji"]),
            channel=result["channel"],
            has_lul=result["has_lul"]

        )
        for result in results
    ]
    return data


@query.field("channel")
async def resolve_channels(_, info, channel: str) -> Dict[str, Any]:
    channel_lowered: str = channel.lower()

    row: Mapping = await database.fetch_one(
        query=channel_metrics_query,
        values=dict(channel=channel_lowered)
    )

    sentiment: float = row["chat_sentiment"] if row["chat_sentiment"] else 0.0
    data = dict(
        channel=channel_lowered,
        chat_sentiment=sentiment,
        messages_per_minute=row["messages_per_minute"],
        lulz_per_minute=row["lulz_per_minute"],
        sentiment_emoji=emojize(emoji_from_score(sentiment))
    )

    return data


@subscription.source("streamChannel")
async def message_generator(
        _,  # Parent obj/entity
        info: dict,
        nickname: str,
        token: str,
        channel: str
) -> AsyncGenerator[Dict[str, Any], None]:
    twitch_client = TwitchIRCClient(nickname, token)
    async for msg in twitch_client.stream(channel):
        print(msg)
        msg["created_at"] = str(msg["created_at"])
        msg["channel"] = channel
        await redis.publish(f"TwitchMessageCreated", json.dumps(msg))
        yield msg


@subscription.field("streamChannel")
async def resolve_stream_channel(msg, info, nickname, token, channel):
    return msg

schema = make_executable_schema(type_defs, [query, subscription])
