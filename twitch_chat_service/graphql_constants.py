"""
Constants used for graphql websocket control flow.
"""
import enum


class GQLEnum(enum.Enum):
    CONNECTION_INIT = "connection_init"  # Client -> Server
    CONNECTION_ACK = "connection_ack"  # Server -> Client
    CONNECTION_ERROR = "connection_error"  # Server -> Client
    CONNECTION_KEEP_ALIVE = "ka"  # Server -> Client
    CONNECTION_TERMINATE = "connection_terminate"  # Client -> Server
    START = "start"  # Client -> Server
    DATA = "data"  # Server -> Client
    ERROR = "error"  # Server -> Client
    COMPLETE = "complete"  # Server -> Client
    STOP = "stop"  # Client -> Server