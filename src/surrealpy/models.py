class SurrealID:
    __slots__ = "_members"
    _members: tuple[str, str]

    def __init__(self, table: str, uid: str | None = None):
        if uid is None:
            try:
                table, uid = table.split(":")
            except ValueError:
                raise ValueError(f"SurrealID should be in the form <tbl>:<oid>, got '{table}'")

        object.__setattr__(self, "_members", (str(table), str(uid)))

    def __eq__(self, other):
        return issubclass(other.__class__, self.__class__) and self._members == other._members

    def __hash__(self):
        return hash(self._members)

    def __repr__(self):
        return ":".join(self._members)

    @property
    def table(self):
        return self._members[0]

    @property
    def uid(self):
        return self._members[1]
