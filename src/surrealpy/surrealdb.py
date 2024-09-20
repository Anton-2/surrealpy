import asyncio
from itertools import count
from typing import Any
from uuid import UUID

from websockets.asyncio import client

from .cbor import cbor_dumps, cbor_loads


class SurrealDBError(Exception):
    code: int
    message: str

    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return f"{self.message} (#{self.code})"


class SurQLError(Exception):
    pass


STOP_TOKEN = object()


class LiveResult:
    def __init__(self, uuid):
        self.uuid = uuid
        self.queue = asyncio.Queue()

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.queue:
            raise StopAsyncIteration

        ret = await self.queue.get()
        if ret is STOP_TOKEN:
            raise StopAsyncIteration
        return ret

    def put(self, value):
        if self.queue:
            self.queue.put_nowait(value)

    def close(self):
        if self.queue:
            self.queue.put_nowait(STOP_TOKEN)
            self.queue = None


class SurrealDB:
    def __init__(self, url="ws://localhost:8000"):
        self.url = f"{url}/rpc"
        self.cnt = count(1)

        self.pending = {}
        self.loop = None
        self.ws = None

    #
    # async context manager stuff
    #
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args):
        await self.close()
        return False

    def _handle_live(self, uuid, result):
        live = self.pending.get(uuid)
        if not live:
            print(f"No Live for {uuid}")
            return
        live.put(result)

    async def _recv(self):
        assert self.ws
        while True:
            msg = await self.ws.recv(decode=False)
            data = cbor_loads(msg)
            cmdid = data.get("id")

            if cmdid is None:
                result = data.get("result")
                live_uuid = result.get("id") if result else None
                if live_uuid is not None:
                    self._handle_live(live_uuid, result)
                else:
                    print(f"recv bad msg {msg}")
                continue

            pending = self.pending.pop(cmdid, None)
            if pending is None:
                print(f"No Future for {msg}")
                continue
            (fut, live) = pending
            if not fut.cancelled():
                try:
                    error = data.get("error")
                    if error:
                        code = error.get("code", 0)
                        msg = error.get("message", "?")
                        raise SurrealDBError(code, msg)
                    else:
                        result = data["result"]
                        if live:
                            uuid = result if isinstance(result, UUID) else result[0]["result"]
                            if not isinstance(uuid, UUID):
                                raise SurQLError(f"Expected live query result, got {result}")
                            live = LiveResult(uuid)
                            self.pending[uuid] = live
                            fut.set_result(live)
                        else:
                            fut.set_result(result)
                except Exception as exp:
                    fut.set_exception(exp)

    async def connect(self):
        """Connects to the database endpoint"""
        self.ws = await client.connect(self.url, subprotocols=["cbor"])
        self.loop = asyncio.get_running_loop()
        self.rtask = self.loop.create_task(self._recv())

    async def close(self):
        """Closes the persistent connection to the database"""
        # TODO: kill all live queries still running
        if not self.ws:
            return
        self.rtask.cancel()
        await self.ws.close()

    async def cmd(self, method: str, *params, live=False):
        """Send a command to surrealdb, and wait for the result"""
        assert self.loop and self.ws, "You need to call and await connect before issung commands"
        cmdid = next(self.cnt)
        fut = self.loop.create_future()
        self.pending[cmdid] = (fut, live)
        msg = cbor_dumps(dict(id=cmdid, method=method, params=params))
        await self.ws.send(msg)
        return await fut

    # TODO: handle unset and no changes (None/null)
    async def use(self, ns: str, db: str) -> None:
        """Specifies or unsets the namespace and/or database for the current connection."""

        await self.cmd("use", ns, db)

    async def signin(self, params: dict[str, Any]) -> str:
        """This method allows you to signin as a root, NS, DB user or with an access method against SurrealDB"""

        return await self.cmd("signin", params)

    async def authenticate(self, token: str) -> None:
        """This method allows you to authenticate a user against SurrealDB with a token"""

        await self.cmd("authenticate", token)

    async def invalidate(self) -> None:
        """This method will invalidate the user's session for the current connection"""

        await self.cmd("invalidate")

    async def let(self, name: str, value: Any) -> None:
        """This method defines a variable on the current connection"""

        await self.cmd("let", name, value)

    async def unset(self, name: str) -> None:
        """This method removes a variable from the current connection"""

        await self.cmd("unset", name)

    async def live(self, table: str, diff: bool = False) -> LiveResult:
        """This methods initiates a live query for a specified table name"""

        return await self.cmd("live", table, diff, live=True)

    async def kill(self, query_uuid: str) -> None:
        """This method kills an active live query"""
        await self.cmd("kill", query_uuid)
        live = self.pending.pop(query_uuid, None)
        if live:
            live.close()

    async def query(self, statment: str, **params):
        """This method executes a custom query with optional variables"""
        response = await self.cmd("query", statment, params)

        first, *rest = response
        if rest:
            raise SurQLError("This statment returns multiple results. Use raw_query instead")

        status = first.get("status")
        result = first.get("result")
        if status == "OK":
            return result
        else:
            raise SurQLError(result)

    async def select(self, name: str) -> Any:
        """This method selects either all records in a table or a single record"""
        return await self.cmd("select", name)

    async def create(self, name: str, content: Any) -> Any:
        """This method creates a record either with a random or specified ID"""
        return await self.cmd("create", name, content)

    async def update(self, name: str, content: Any) -> Any:
        """This method replaces either all records in a table or a single record with specified data"""
        return await self.cmd("update", name, content)

    async def delete(self, name: str) -> Any:
        """This method deletes either all records in a table or a single record"""
        return await self.cmd("delete", name)

    async def live_query(self, statment: str, **params):
        return await self.cmd("query", statment, params, live=True)

    async def raw_query(self, statments: str, **params):
        return await self.cmd("query", statments, params)
