import doctest

import time_utils


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(time_utils))
    return tests


if __name__ == '__main__':
    doctest.testmod(time_utils)
