from multiprocessing import Process

import pytest
import requests

import proxypool.proxy_server as proxy_server
from proxypool.config import HOST, PORT


@pytest.fixture
def api(db):
    db.put_list(['127.0.0.1:80', '127.0.0.1:443', '127.0.0.1:1080'])
    proxy_server.conn = db # replace with test db
    server = Process(target=proxy_server.server_run)
    server.start()
    yield 'http://{0}:{1}'.format(HOST, PORT)
    db.pop_list(3)
    server.terminate()

def test_server_get(db, api):
    proxies = ['127.0.0.1:80', '127.0.0.1:443', '127.0.0.1:1080']

    assert requests.get('{0}/get'.format(api)).json()['proxies'][0] in proxies

    assert requests.get('{0}/get/3'.format(api)).json()['proxies'].sort() == proxies.sort()

    assert requests.get('{0}/get/10'.format(api)).json()['proxies'].sort() == proxies.sort()

    assert db.count == requests.get('{0}/count'.format(api)).json()['count']

