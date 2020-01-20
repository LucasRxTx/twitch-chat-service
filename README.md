Twitch Chat Analytics
===

A micro-service platform for streaming Twitch IRC channel messages and
analysing the results.  Subscription to chat, and querying analytics
are available through a GraphQL endpoint.

Things you will need:
- A twitch oauth2 token available from Twitch [here](https://twitchapps.com/tmi/).
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

# Known issues
Websocket connection can be flaky.  Does not end connections properly sometimes.
Multiple subscriptions has not been tested or attempted 😱 (Does it work?)
