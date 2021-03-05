import datetime
import unittest

import trackd

import pathlib
import sqlite3

from typing import Iterable


class SpanStoreTest(unittest.TestCase):

    def test_retrieves_same_as_saved(self):
        storage = trackd.SpanStorage(db_path=':memory:')
        now = trackd.now()
        span = trackd.Span(
                span_name='span',
                start=now,
                end=now + datetime.timedelta(minutes=5),
        )

        storage.add(span)

        (retrieved,) = list(storage.query())
        self.assertEqual(span, retrieved)


if __name__ == '__main__':
    unittest.main()
