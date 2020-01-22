import os
import requests
from starlette.applications import Starlette
from starlette.routing import Route, WebSocketRoute
from starlette.responses import JSONResponse, HTMLResponse
from ariadne.asgi import GraphQL
from twitch_chat_service.resolvers import schema
from twitch_chat_service.subscriptions import TwitchGQLSubscription
from twitch_chat_models.models import init_database, database

# TODO: Move to a conf file
client_id = os.environ["TWITCH_CLIENT_ID"]
client_secret = os.environ["TWITCH_CLIENT_SECRET"]


async def get_auth_token(code):
    url = "https://id.twitch.tv/oauth2/token"
    params = dict(
        client_id=client_id,
        client_secret=client_secret,
        code=code,
        grant_type="authorization_code",
        redirect_uri="http://localhost:8000/auth/redirect"
    )

    resp = requests.post(url, params=params)
    try:
        return resp.json()
    except ValueError:
        return {}


async def auth(request):
    """ GET /auth """
    params = dict(
        client_id=client_id,
        redirect_uri="http://localhost:8000/auth/redirect",
        response_type="code",
        force_verify=True,
        scope="chat:read+chat:edit+channel:moderate+whispers:read+whispers:edit"
    )
    params = "&".join([f"{k}={v}" for k, v in params.items()])
    url = f"https://id.twitch.tv/oauth2/authorize?{params}"

    # TODO: Make fancy login page
    return HTMLResponse(f"<a href='{url}'>login<a>", 200)


async def auth_redirect(request):
    """ GET or POST /auth/redirect """
    args = request.query_params
    code = args.get("code")
    scope = args.get("scope")
    state = args.get("state")
    data = dict(
        code=code,
        scope=scope,
        state=state
    )
    resp_data = await get_auth_token(code=data["code"])
    return JSONResponse(resp_data, 200)


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
    Route("/auth", endpoint=auth),
    Route("/auth/redirect", endpoint=auth_redirect),
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
