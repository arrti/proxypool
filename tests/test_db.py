import os.path
import time

import pytest

from proxypool.errors import ProxyPoolEmptyError


slow = pytest.mark.skipif(
    not pytest.config.getoption("--runslow"),
    reason="need --runslow option to run"
)


def test_db_base(db):
    db.put('abc')
    assert db.get() == b'abc'
    assert db.count == 1

    assert db.pop() == b'abc'
    assert db.count == 0

    db.put_list(['proxy', 'pool', 'redis'])
    assert db.get_list(3) == [b'proxy', b'pool', b'redis']
    assert db.count == 3

    db.put('proxy')
    assert db.get_list(3) == [b'proxy', b'pool', b'redis']
    assert db.count == 3

    db.put('python')
    assert db.count == 4

    assert db.pop_list(4) == [b'proxy', b'pool', b'redis', b'python']
    assert db.count == 0

@slow
def test_db_empty(db):
    with pytest.raises(ProxyPoolEmptyError):
        db.get()

@slow
def test_db_cache(db,tmpdir):
    p = tmpdir.mkdir('db').join('proxypool.txt')
    p.write('proxy pool')
    content = p.read()
    assert content == 'proxy pool'

    mtime = int(os.path.getmtime(str(p)))
    db.set_cache('proxypool', content, mtime)
    assert db.get_cache('proxypool') == (content.encode('utf-8'), str(mtime).encode('utf-8'))

    content2 = p.read()
    mtime2 = int(os.path.getmtime(str(p)))
    db.set_cache('proxypool', content2, mtime2, 6)
    time.sleep(2)
    assert db.get_cache('proxypool') == (content.encode('utf-8'), str(mtime).encode('utf-8'))
    time.sleep(5)
    assert db.get_cache('proxypool') == (None, None)

    p.write('is a python app')
    content3 = p.read()
    mtime3 = int(os.path.getmtime(str(p)))
    assert content3 == 'is a python app'
    db.set_cache('proxypool', content3, mtime3, 6)
    time.sleep(4)
    assert db.get_cache('proxypool') != (content.encode('utf-8'), str(mtime).encode('utf-8'))
    assert db.get_cache('proxypool') == (content3.encode('utf-8'), str(mtime3).encode('utf-8'))

