import datetime
import os
import databases
import sqlalchemy as sa
import pymysql
import time
# from aiomysql.sa import create_engine
from typing import Optional
from aredis import StrictRedis
from sqlalchemy import event

with open("./twitch_chat_models/sql/channel_metrics.sql", "r") as f:
    channel_metrics_query = f.read()

#
# Utility functions
#
def now():
    return datetime.datetime.now(datetime.timezone.utc)    


def create_db_uri(driver: str):
    if "sqlite" in os.environ["DB_HOST"]:
        return "sqlite:///:memory:"

    username = os.environ["DB_USER"]
    password = os.environ["DB_PASS"]
    host = os.environ["DB_HOST"]
    port = os.environ["DB_PORT"]
    database = os.environ["DB_DB"]

    return f"mysql+{driver}://{username}:{password}@{host}:{port}/{database}?charset=utf8mb4"

#
# Database table definitions.
#
metadata = sa.MetaData()

messages = sa.Table(
    "messages",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("nickname", sa.Unicode(255), nullable=False),
    sa.Column("body", sa.Unicode(800), nullable=False),
    sa.Column("sentiment", sa.Float, nullable=True),
    sa.Column("created_at", sa.DateTime, default=now),
    sa.Column("sentiment_emoji", sa.Unicode(255), nullable=False),
    sa.Column("has_lul", sa.Integer, nullable=False),
    sa.Column("channel", sa.Unicode(255), nullable=False)
)

channels = sa.Table(
    "channels",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("streamer", sa.Unicode(255), nullable=False),
    sa.Column("msg_rate", sa.Float, default=0.0),
    sa.Column("emoji", sa.Unicode(10), default="\U0001F610")
)

#
# Create tables if none exsists
#
def init_database():
    connected = False
    while not connected:
        # Database may not be available, loop untill connection can be established.
        try:
            # Create tables with syncronous pymysql
            # because `await` not available outside of function.
            is_dev = os.getenv("ENV") == "development"
            engine = sa.create_engine(create_db_uri("pymysql"), echo=is_dev)
            metadata.create_all(engine)
        except (pymysql.err.OperationalError, pymysql.err.InternalError):
            # Exception raised if connection dropped or not connected.  Try again.
            time.sleep(1)
            pass
        else:
            connected = True

# Use aiomysql for everything elese.
database = databases.Database(create_db_uri("aiomysql"))

# Redis used for pub/sub
redis = StrictRedis(
    host=os.environ["REDIS_HOST"],
    port=int(os.environ["REDIS_PORT"]),
    db=int(os.environ["REDIS_DB"])
)
