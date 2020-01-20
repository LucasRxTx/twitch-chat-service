import requests
import flask
import json
import os

client_id = os.environ["TWITCH_CLIENT_ID"]
client_secret = os.environ["TWITCH_CLIENT_SECRET"]

server = 'irc.chat.twitch.tv'
port = 6667


def get_auth_token(code):
    url = "https://id.twitch.tv/oauth2/token"
    params = dict(
        client_id=client_id,
        client_secret=client_secret,
        code=code,
        grant_type="authorization_code",
        redirect_uri="http://localhost:5000/auth/redirect"
    )
    resp = requests.post(url, params=params)

    return resp.json()


app = flask.Flask(__name__)


@app.route("/auth/s2s", methods=["GET"])
def hmm():
    return get_auth_page(), 200


@app.route("/auth", methods=["GET"])
def auth():
    params = dict(
        client_id=client_id,
        redirect_uri="http://localhost:5000/auth/redirect",
        response_type="code",
        force_verify=True,
        scope="chat:read+chat:edit+channel:moderate+whispers:read+whispers:edit"
    )
    params = "&".join([f"{k}={v}" for k, v in params.items()])
    url = f"https://id.twitch.tv/oauth2/authorize?{params}"

    return f"<a href='{url}'>login<a>", 200


@app.route("/", methods=["GET", "POST"])
@app.route("/auth/redirect", methods=["GET", "POST"])
def auth_redirect():
    args = flask.request.args
    code = args.get("code")
    scope = args.get("scope")
    state = args.get("state")
    data = dict(
        code=code,
        scope=scope,
        state=state
    )
    resp_data = get_auth_token(code=data["code"])
    return json.dumps(resp_data), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
