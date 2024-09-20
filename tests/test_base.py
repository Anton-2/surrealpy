import datetime
import uuid

from surrealpy import SurrealDB, SurrealID


async def test_connect():
    async with SurrealDB() as db:
        assert await db.cmd("version")


async def test_signin():
    async with SurrealDB() as db:
        ret = await db.signin({"user": "root", "pass": "root"})
        assert isinstance(ret, str)


async def test_base_types():
    data = dict(string="Test Name", integer=1, float=2.2, true_bool=True, false_bool=False, none=None)
    async with SurrealDB() as db:
        await db.signin({"user": "root", "pass": "root"})
        ret = await db.query("$val", val=data)
        assert ret == data


async def test_datetime_types():
    data = dict(
        date=datetime.date.today(),
        datetime=datetime.datetime.now(tz=datetime.UTC),
        duration=datetime.timedelta(days=2, seconds=4, milliseconds=34),
    )
    async with SurrealDB() as db:
        await db.signin({"user": "root", "pass": "root"})
        ret = await db.query("$val", val=data)
        # SurrealDB as only a datetime type, convert back to date
        ret["date"] = ret["date"].date()
        assert ret == data


async def test_id_types():
    data = dict(uuid=uuid.uuid4(), sid=SurrealID("test", "test"))
    async with SurrealDB() as db:
        await db.signin({"user": "root", "pass": "root"})
        ret = await db.query("$val", val=data)
        assert ret == data
