from starlette.applications import Starlette
from starlette.routing import Route, WebSocketRoute
from ariadne.asgi import GraphQL
from twitch_chat_service.resolvers import schema
from twitch_chat_service.subscriptions import TwitchGQLSubscription
from twitch_chat_models.models import init_database, database


async def websocket_route(websocket):
    """ Websocket available at ws://0.0.0.0:8000/ """
    try:
        await websocket.accept("graphql-ws")
        while True:
            request_raw: str = await websocket.receive_text()
            twitch_subscription = TwitchGQLSubscription(websocket, schema)
            await twitch_subscription.subscribe(request_raw)
        else:
            print("closing")
            await websocket.close()
    except KeyboardInterrupt:
        await websocket.close()
        raise


# Graphql playground available at http://0.0.0.0:8000/
routes = [
    Route("/", endpoint=GraphQL(schema, debug=True)),
    WebSocketRoute("/", endpoint=websocket_route)
]


def create_app() -> Starlette:
    init_database()
    return Starlette(
        routes=routes,
        on_startup=[database.connect],
        on_shutdown=[database.disconnect]
    )
