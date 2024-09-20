# README

surrealpy is another Python tool for working with [SurrealDB](https://surrealdb.com) v2.x.

It is **asynchronous** and **unofficial**, so if you need an
  - Official client, go [here](https://github.com/surrealdb/surrealdb.py). But the current release v0.3.2 is not really usable in async environments [Bug: Concurrency issues](https://github.com/surrealdb/surrealdb.py/issues/101)
  - Unofficial but up to date **synchronous** client, go [here](https://github.com/kotolex/surrealist)

This is a very rough release, it works for me (python 3.12 on macos) but needs to be tested on more environments.

#### Key features: ####

 * Asynchronous
 * CBOR over websocket: live queries, small data transfers, full type conversion between surrealdb and python.
 * Only two dependencies (websockets and CBOR)
 * Not well documented
 * Not well tested
 * Only compatible with SurrealDB 2.x

#### Plans: ####
 * Add all SDK methods (missing: signup, graphql, run, insert, insert_relation, upsert, relate, merge, patch)
 * Documentation
 * Testing

#### Maybe ?: ####
 * Move to [websocket-client](https://github.com/websocket-client/websocket-client) ?
 * optional adapter between geometry objects and [Shapely](https://shapely.readthedocs.io/en/stable/)
 * optional adapter for pydantic

### Installation ###

Via pip:

`pip install 'git+https://github.com/Anton-2/surrealpy.git'`.
