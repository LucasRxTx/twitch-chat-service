Twitch Chat Analytics
===

A micro-service platform for streaming Twitch IRC channel messages and
analysing the results.  Subscription to chat, and querying analytics
are available through a GraphQL endpoint.

Things you will need:
- A twitch oauth2 token available from Twitch [here](https://twitchapps.com/tmi/).  DONOT INCLUDE "oath:" WITH THE TOKEN!
- A flask oauth service is available at `twitch_cha_service/irc`.  It works but will be moved to a starlette handler.

# to run

```docker-compose up -d db && docker-compose up -d redis```

then:

```docker-compose up```

Later iterations will allow just `docker-compose up` for inital runs.  Currently
the database has to make tables before accepting connections.  If running every
thing together, connections will fail due to the database not being ready for
connections.


The graphql playground is available at:
http://localhost:8000/

# Queries to try

### Subscribe to a channel and stream messages
``` graphql
subscription streamChannel {
  streamChannel(
    nickname: "your twitch nickname",
    token: "your oath2 token from twitch",
    channel: "name of channel to subscribe"
  ){
    nickname
    body
    created_at
    channel
  }
}
```

### Get chat analytics
Once you are streaming some messages, you can query the channel for analytics

``` graphql
query {
  channel(channel: "name of channel you are streaming") {
	lulz_per_minute
    messages_per_minute
    chat_sentiment
    sentiment_emoji
  }
}
```

# Troubleshooting
Im having trouble with database connections...
- Delete the volume for the database and `docker-compose up -d db` to start
the database from scratch.  `docker-compose up` dependent services seperately

I connect, but no messages are streaming...
- Is the channel still open?
- Is you oauth token valid? (DONOT INCLUDE `oath:` with your token)
- Channel name should not include a `#`

# Known issues
Websocket connection can be flaky.  Does not end connections properly sometimes.
Multiple subscriptions has not been tested or attempted 😱 (Does it work?).
Can another user see your stream?!? 🙀

If your auth token expires, or is invalid it will look like you have
connected but nothing will happen.

# Repos used as reference
During development I used a few repositories to learn how to use websockets
with Starlette and GraphQL.  You can view them here to see how I took
reference material, learned from it, improved it and made it my own.

- [patrys](https://github.com/patrys/starlette-ariadne/tree/31d9354b26f03c4ef7af19ca0f97d5f859059282)
- [fgshun](https://gist.github.com/fgshun/fe96c21b2de743a88778e4f729510190)
