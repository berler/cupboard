"""A persistent dictionary-like object

This works in a very similar way to shelve, except that this uses an
sqlite file, and values are stored as json. This means that unlike
shelve, only json serializable values can be used.

Because the data format is not python-specific (sqlite and json
serialized values), you can easily view/edit the file in other languages
or with other tools.

The sqlite file uses the following schema:

    CREATE TABLE cupboard (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )

Typical usage:

    import cupboard

    db = cupboard.open('db-filename')

    # use db just like a dict:
    db['foo'] = 123
    db['bar'] = ['a', 'b', 42]
    db['baz'] = db['foo'] + 3

    print(len(db))         # 3
    print(list(db.keys())) # ['bar', 'baz', 'foo']

    db.close()

You may also use a cupboard as a context manager to avoid needing to
explicitly call close():

    with cupboard.open('db-filename') as db:
        db['foo'] = 123
        db['bar'] = ['a', 'b', 42]
        db['baz'] = db['foo'] + 3

Note that cupboard is not thread-safe. You should only use a cupboard
from the thread in which it was opened.
"""
__author__ = 'Steven Berler'
__license__ = 'MIT'
__copyright__ = 'Copyright (c) 2016 Steven Berler'
__version__ = '0.1.0'

import collections as _collections
import json as _json
import sqlite3 as _sqlite3

_CREATE_QUERY = 'CREATE TABLE IF NOT EXISTS cupboard (key TEXT PRIMARY KEY, value TEXT NOT NULL)'
_GET_QUERY = 'SELECT value FROM cupboard WHERE key = ?'
_SET_QUERY = 'INSERT OR REPLACE INTO cupboard VALUES (?, ?)'
_DEL_QUERY = 'DELETE FROM cupboard WHERE key = ?'
_ITER_QUERY = 'SELECT key FROM cupboard'
_LEN_QUERY = 'SELECT COUNT(*) FROM cupboard'

class CupboardClosedError(ValueError):
    """Error that occurs when a :class:`Cupboard` is attempted to be
    used after it has been closed"""
    pass

class Cupboard(_collections.MutableMapping):
    """A Cupboard acts like a dict but is backed by a sqlite database.

    Only strings may be used as keys. If something other than a string
    is attempted to be used as a key, a :class:`TypeError` will be
    raised.

    Only json-serializable data may be used as values. This means that
    values may only be of type str, int, float, bool, list, dict, or
    None.
    """

    __slots__ = ['writeback', '_cache', '_conn']

    def __init__(self, filename, flag='c', writeback=False):
        if flag != 'c':
            raise NotImplementedError('Only flag="c" (the default) is currently implemented')
        self.writeback = writeback
        self._cache = {}
        self._conn = _sqlite3.connect(filename)
        self._conn.execute(_CREATE_QUERY)

    @property
    def cache(self):
        """A cache which only contains mutable values in the Cupboard.

        This is only used when writeback=True.
        """
        if self._cache is None:
            raise CupboardClosedError('invalid operation. cupboard is closed')
        return self._cache

    @property
    def conn(self):
        """The sqlite connection"""
        if self._conn is None:
            raise CupboardClosedError('invalid operation. cupboard is closed')
        return self._conn

    def __iter__(self):
        for row in self.conn.execute(_ITER_QUERY):
            yield row[0]

    def __len__(self):
        row = self.conn.execute(_LEN_QUERY).fetchone()
        if row is None:
            return 0
        return row[0]

    def _update_cache(self, key, value):
        self.cache.pop(key, None)
        if self.writeback and isinstance(value, (dict, list)):
            self.cache[key] = value

    def __getitem__(self, key):
        if not isinstance(key, str):
            raise TypeError('keys in a Cupboard must always be strings. {} is not a string'.format(repr(key)))

        if key in self.cache:
            return self.cache[key]

        row = self.conn.execute(_GET_QUERY, (key,)).fetchone()
        if row is None:
            raise KeyError(key)
        jstr = row[0]
        value = _json.loads(jstr)

        self._update_cache(key, value)

        return value

    def __setitem__(self, key, value):
        if not isinstance(key, str):
            raise TypeError('keys in a Cupboard must always be strings. {} is not a string'.format(repr(key)))

        jstr = _json.dumps(value)
        with self.conn:
            self.conn.execute(_SET_QUERY, (key, jstr))

        self._update_cache(key, value)

    def __delitem__(self, key):
        with self.conn:
            self.conn.execute(_DEL_QUERY, (key,))

        self.cache.pop(key, None)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __del__(self):
        if getattr(self, '_conn', None) is not None:
            self.close()

    def sync(self):
        """If writeback=True, this will write any changes that have been
        made to any values that are mutable (dicts or lists). If
        writeback=False, this will not do anything.

        Note that sync() is called automatically when close() is called.
        """
        if not self.cache:
            return

        with self.conn:
            for key, value in self.cache.items():
                jstr = _json.dumps(value)
                self.conn.execute(_SET_QUERY, (key, jstr))

    def close(self):
        """Close the Cupboard.

        You should always call this method when you are done using a
        Cupboard (ideally in a finally block). Failure to call this may
        result in a corrupt sqlite database.

        If the Cupboard is used as a context manager, close is called
        automatically.
        """
        try:
            self.sync()
            self.conn.close()
        except CupboardClosedError:
            pass
        finally:
            self._conn = None
            self._cache = None

def open(filename, flag='c', writeback=False):
    """Open a :class:`Cupboard` for reading and writing. This behaves
    similarly to :func:`shelve.open`.

    The filename will be used to open or create an sqlite file. Unlike
    shelve, the filename will be used exactly without any added
    extension.

    The flag and writeback optional parameters have the exact same
    meaning as in shelve. However 'c' (the default value) is currently
    the only supported value for flag. This means that the database file
    will be created if it does not already exist, and the file will be
    opened for both reading and writing.
    """
    return Cupboard(filename, flag=flag, writeback=writeback)
