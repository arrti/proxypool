from pathlib import Path
import sys

import pytest


# add project path to sys.path in case 'proxypool' was not installed
current = Path(__file__).parent.parent
path = str(current)
sys.path.append(path)

def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true",
                     help="run slow tests")
    parser.addoption("--runptjs", action="store_true",
                     help="run tests using phantomjs")

@pytest.fixture(scope='session')
def db():
    from proxypool.db import RedisClient as rc
    return rc('127.0.0.1', 6379) # make sure this redis instance was running before testing
