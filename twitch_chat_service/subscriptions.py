import json
import graphql
from graphql.execution.execute import ExecutionResult
from graphql.subscription.map_async_iterator import MapAsyncIterator
from twitch_chat_service.graphql_constants import GQLEnum
from typing import Optional, Union, AsyncIterator, Callable, Dict


class TwitchGQLSubscription:
    """ Handle websocket connection for GraphQL Subscription to Twitch """
    def __init__(self, websocket, schema):
        self.websocket = websocket
        self.schema = schema

    def parse_request(self, request_raw: str) -> dict:
        """ Parse incoming websocket request. """
        request: dict = json.loads(request_raw)
        request["raw"] = request_raw
        return request

    def create_subscription_payload(self, request) -> dict:
        payload: dict = request["payload"]
        data = dict(
            query=payload.get("query"),
            variables=payload.get("variables"),
            operation_name=payload.get("operationName")
        )
        source: graphql.Source = graphql.Source(payload.get("query", ""))
        document: graphql.DocumentNode = graphql.parse(source)

        return dict(
            schema=self.schema,  # compiled graphql schema
            document=document,  # query document
            root_value=None,  # We are root so `root_value` is None.
            context_value=dict(request=request["raw"]),  # raw request as str.
            variable_values=data["variables"],  # variables passed in.
            operation_name=data["operation_name"],  # name of operation to perform.
        )

    async def handle_connection_init(self, request: dict):
        """ Handle `GQLEnum.CONNECTION_INIT` sent from client. """
        print("> ACK")
        ack_resp = json.dumps(
            dict(type=GQLEnum.CONNECTION_ACK.value)
        )
        await self.websocket.send_text(ack_resp)

    async def handle_connection_terminate(self, request: dict):
        """ Handle `GQLEnum.CONNECTION_TERMINATE` sent from client. """
        print("> CONNECTION_TERMINATE")
        pass

    async def handle_start(self, request: dict):
        """ Handle `GQLEnum.START` sent from client. """
        print("start")
        operation_id: Optional[str] = request.get("id")
        subscription_payload: dict = self.create_subscription_payload(request)

        # graphql.subscribe returns
        # ExecutionResult: on error
        # AsyncIterator[ExecutionResult]: on success
        results: Union[AsyncIterator[ExecutionResult], ExecutionResult] = \
            await graphql.subscribe(**subscription_payload)

        if isinstance(results, ExecutionResult):
            await self.send_error_response(results, operation_id)
        else:
            await self.stream_channel(results, operation_id)

    async def handle_stop(self, request: dict):
        """ Handle `GQLEnum.STOP` sent from client. """
        pass

    async def send_error_response(self, results, operation_id):
        # set default error message.
        payload = dict(
            message=dict(
                message="Unhandled error occoured",
                locations=[],
                path=""
            )
        )
        # Set error message if value is available
        if results.errors is not None and len(results.errors) > 0:
            payload = dict(message=graphql.format_error(results.errors[0]))

        json_response: str = json.dumps(dict(
            type=GQLEnum.ERROR.value,
            id=operation_id,
            payload=payload
        ))
        await self.websocket.send_text(json_response)

    async def stream_channel(self, results, operation_id):
        async for result in results:
            resp = dict()
            print("result:", result)
            if result and result.data:
                resp = dict(
                    type=GQLEnum.DATA.value,
                    id=operation_id,
                    payload=dict(data=result.data)
                )
            if result and result.errors:
                resp = dict(
                    errors=[graphql.format_error(e) for e in result.errors]
                )
            print("payload", resp)
            json_response: str = json.dumps(dict(
                type=GQLEnum.DATA.value,
                id=operation_id,
                payload=resp
            ))
            await self.websocket.send_text(json_response)

        json_response: dict = json.dumps(dict(
            type=GQLEnum.COMPLETE.value,
            id=operation_id
        ))
        await self.websocket.send_text(json_response)

    async def subscribe(self, request_raw):
        request: dict = self.parse_request(request_raw)
        message_type: Optional[str] = request.get("type")

        handler_map: Dict[GQLEnum, Callable[[dict], None]] = {
            GQLEnum.CONNECTION_INIT: self.handle_connection_init,
            GQLEnum.CONNECTION_TERMINATE: self.handle_connection_terminate,
            GQLEnum.START: self.handle_start,
            GQLEnum.STOP: self.handle_stop
        }

        handler: Callable[[dict], None] = handler_map.get(GQLEnum(message_type))
        if handler:
            await handler(request)
        else:
            print(f"Unhandled control event for request type: {message_type}")
            print("request_raw:", request["raw"])
