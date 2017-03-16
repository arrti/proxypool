import pytest
from pathlib import Path
import sys


# add project path to sys.path in case 'proxypool' was not installed
current = Path(__file__).parent.parent
parent = current.parent
path = str(current) if 'ProxyPool' in str(current) else str(parent)
sys.path.append(path)


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true",
                     help="run slow tests")
    parser.addoption("--runptjs", action="store_true",
                     help="run tests using phantomjs")



@pytest.fixture(scope='session')
def db():
    from proxypool.db import RedisClient as rc
    return rc('127.0.0.1', '6379') # make sure this redis instance was running before testing
