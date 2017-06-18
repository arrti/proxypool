from multiprocessing import Process
from time import sleep

import pytest
import requests

import proxypool.proxy_server as proxy_server
from proxypool.config import HOST, PORT, SSL_ON, CA_CRT


@pytest.fixture
def api(db):
    db.put_list(['127.0.0.1:80', '127.0.0.1:443', '127.0.0.1:1080'])
    proxy_server.conn = db # replace with test db
    server = Process(target=proxy_server.server_run)
    server.start()
    sleep(0.5)
    if SSL_ON:
        yield 'https://{0}:{1}'.format(HOST, PORT)
    else:
        yield 'http://{0}:{1}'.format(HOST, PORT)
    db.pop_list(3)
    server.terminate()

def test_server_get(db, api):
    proxies = ['127.0.0.1:80', '127.0.0.1:443', '127.0.0.1:1080']
    verify = True
    if SSL_ON and CA_CRT:
        verify = CA_CRT

    assert requests.get('{}/proxies/'.format(api),
                        verify=verify).json()['proxies'][0] in proxies

    assert requests.get('{}/proxies/proxy'.format(api),
                        verify=verify).status_code == 404

    assert requests.get('{}/proxies/0'.format(api),
                        verify=verify).json()['count'] == 0

    assert requests.get('{}/proxies/3'.format(api),
                        verify=verify).json()['proxies'].sort() == proxies.sort()

    assert requests.get('{}/proxies/10'.format(api),
                        verify=verify).json()['proxies'].sort() == proxies.sort()

    assert db.count == requests.get('{}/proxies/count'.format(api),
                                    verify=verify).json()['count']

