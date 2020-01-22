import datetime
import os
import databases
import sqlalchemy as sa
import pymysql
import time
# from aiomysql.sa import create_engine
from typing import Optional
from aredis import StrictRedis


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


def ensure_db_connection():
    max_reties = os.getenv("DB_CONNECT_RETRIES", 10)
    connected = False
    while not connected:
        # Database may not be available, loop untill connected or max retires.
        try:
            # Create tables with syncronous pymysql
            # because `await` not available outside of function.
            connection = pymysql.connect(
                host=os.environ["DB_HOST"],
                user=os.environ["DB_USER"],
                password=os.environ["DB_PASS"],
                db=os.environ["DB_DB"],
                charset='utf8mb4',
            )
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1=1")
        except Exception:
            max_reties -= 1
            if max_reties <= 0:
                raise RuntimeError("Unable to connect to database.")

            time.sleep(5)
            pass
        else:
            connected = True


#
# Create tables if none exsists
#
def init_database():
    ensure_db_connection()

    is_dev = os.getenv("ENV") == "development"
    engine = sa.create_engine(create_db_uri("pymysql"), echo=is_dev)
    metadata.create_all(engine)

# Use aiomysql for everything elese.
database = databases.Database(create_db_uri("aiomysql"))

# Redis used for pub/sub
redis = StrictRedis(
    host=os.environ["REDIS_HOST"],
    port=int(os.environ["REDIS_PORT"]),
    db=int(os.environ["REDIS_DB"])
)
