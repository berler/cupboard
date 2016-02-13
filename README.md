# cupboard

Cupboard is a python persistent dictionary-like object, similar to shelve.

## Data Format

Cupboard works in a very similar way to shelve, except that it uses an sqlite
file, and values are stored as json. This means that unlike shelve, only json
serializable values can be used.

Because the data format is not python-specific (sqlite and json serialized
values), you can easily view/edit the file in other languages or with other
tools.

The sqlite file uses the following schema:

    CREATE TABLE cupboard (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )

## Typical Usage:

    import cupboard

    db = cupboard.open('db-filename')

    # use db just like a dict:
    db['foo'] = 123
    db['bar'] = ['a', 'b', 42]
    db['baz'] = db['foo'] + 3

    print(len(db))         # 3
    print(list(db.keys())) # ['bar', 'baz', 'foo']

    db.close()

You may also use a cupboard as a context manager to avoid needing to explicitly
call close():

    with cupboard.open('db-filename') as db:
        db['foo'] = 123
        db['bar'] = ['a', 'b', 42]
        db['baz'] = db['foo'] + 3

Cupboard supports the writeback flag, which has the same behavior as shelve:

    with cupboard.open('db-filename', writeback=True) as db:
        db['dict'] = {}
        db['dict']['foo'] = 123  # this only works because writeback=True

Setting writeback=True causes cupboard to cache any mutable values (dicts and
lists), and it will rewrite those objects to the database when the db is closed
in order to save any changes that have been made to them. You can also call
sync() to explicitly write all cached objects to the database without closing
it.

Note that cupboard is not thread-safe. You should only use a cupboard from the
thread in which it was opened.
