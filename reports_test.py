import datetime
import doctest
import unittest

import reports
from time_utils import duration


def make_span(start: str, end: str, name='Span', type_=reports.SpanType.WORK) -> reports.ReportSpan:
    """A helper to create test ReportSpans.

    All but `start` and `end` have sensible default values (for a test).
    `start` and `end` should be text strings in form "HH:MM".
    """

    return reports.ReportSpan(
            name=name,
            type_=type_,
            start=t(start),
            end=t(end))


def t(s):
    h, m = s.split(':')
    return datetime.datetime(year=2000, month=1, day=1, hour=int(h), minute=int(m))


class SplitIntoChunksTest(unittest.TestCase):

    def test_doesnt_split_between_split_points(self):
        self.assertEqual(
                list(reports._split_into_chunks(
                    spans=[make_span(start='10:10', end='10:20')],
                    split_point=duration('30m'))),
                [(t('10:00'), make_span(start='10:10', end='10:20'))])

    def test_splits_in_two_at_split_point(self):
        self.assertEqual(
                list(reports._split_into_chunks(
                    spans=[make_span(start='10:40', end='11:10')],
                    split_point=duration('30m'))),
                [(t('10:30'), make_span(start='10:40', end='11:00')),
                 (t('11:00'), make_span(start='11:00', end='11:10'))])

    def test_splits_in_three(self):
        self.assertEqual(
                list(reports._split_into_chunks(
                    spans=[make_span(start='10:20', end='11:10')],
                    split_point=duration('30m'))),
                [(t('10:00'), make_span(start='10:20', end='10:30')),
                 (t('10:30'), make_span(start='10:30', end='11:00')),
                 (t('11:00'), make_span(start='11:00', end='11:10'))])

    def test_splits_multiple_spans(self):
        self.assertEqual(
                list(reports._split_into_chunks(
                    spans=[make_span(start='10:10', end='10:15'),
                           make_span(start='10:20', end='10:40')],
                    split_point=duration('30m'))),
                [(t('10:00'), make_span(start='10:10', end='10:15')),
                 (t('10:00'), make_span(start='10:20', end='10:30')),
                 (t('10:30'), make_span(start='10:30', end='10:40'))])


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(reports))
    return tests


if __name__ == '__main__':
    unittest.main()
