import datetime
import math
from typing import Any

import cbor2

from .models import SurrealID


def default(encoder: cbor2.CBOREncoder, value: Any):
    match value:
        case SurrealID():
            encoder.encode(cbor2.CBORTag(8, value._members))
        case datetime.timedelta():
            fracpat, intpart = math.modf(value.total_seconds())
            encoder.encode(cbor2.CBORTag(14, [int(intpart), int(fracpat * 1e9)]))
        case _:
            raise ValueError(f"cant encode {repr(value)}")


def tag_hook(decoder: cbor2.CBORDecoder, tag: cbor2.CBORTag):
    if tag.tag == 6:
        return None
    elif tag.tag == 8:
        return SurrealID(*tag.value)
    elif tag.tag == 12:
        seconds, nanoseconds = tag.value
        ret = datetime.datetime.fromtimestamp(seconds, datetime.UTC)
        if nanoseconds:
            ret += datetime.timedelta(microseconds=nanoseconds // 1000)
        return ret
    elif tag.tag == 14:
        sz = len(tag.value)
        if sz == 0:
            return datetime.timedelta()
        elif sz == 1:
            seconds = tag.value[0]
            return datetime.timedelta(seconds=seconds)
        else:
            seconds, ns = tag.value
            return datetime.timedelta(seconds=seconds, microseconds=ns / 1000)

    return tag


def cbor_loads(data: bytes):
    return cbor2.loads(data, tag_hook=tag_hook)


def cbor_dumps(obj: object):
    return cbor2.dumps(obj, timezone=datetime.UTC, date_as_datetime=True, default=default)
