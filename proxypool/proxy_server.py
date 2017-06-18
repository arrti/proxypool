import logging
import logging.config
import asyncio
import os.path
import traceback
import json
import ssl

import yaml
from aiohttp.web import Application, Response, run_app

from proxypool.ext import conn
from proxypool.config import (HOST, PORT, SSL_ON, CERT,
                              KEY, PASSWORD, CA_CRT)
from proxypool.utils import PROJECT_ROOT, _LoggerAsync


logger = _LoggerAsync(is_server=True)

async def index(request):
    name = 'proxy_pool_index'
    path = str(PROJECT_ROOT / 'static/index.html')
    mtime = int(os.path.getmtime(path)) # web page file's modify time
    cache, last = conn.get_cache(name)
    if not cache or int(last) != mtime:
        setup_cache(path, name, mtime)
        cache, last = conn.get_cache(name)
    logger.debug('requested index page',
                 extra={'address': get_address(request), 'method': request.method})
    return Response(body=cache, content_type='text/html')

async def get_ip(request):
    """get single proxy.

    return json data like: "{'count': 1, 'proxies': ['127.0.0.1']}"
    """
    logger.debug('requested ip',
                 extra={'address': get_address(request), 'method': request.method})
    try:
        ip = [conn.get().decode('utf-8')]
    except Exception as e:
        ip = []
        logger.error(e,
                     extra={'address': get_address(request), 'method': request.method})
    return Response(text=jsonify(ip), content_type='application/json') # bytes type data from redis

async def get_ip_list(request):
    """get multi proxies.

    return json data like: "{'count': 10, 'proxies': ['192.168.0.1', ..., '192.168.0.10']}"
    """
    req_count = request.match_info['count']
    if not req_count:
        req_count = 1
    rsp_count = min(int(req_count), conn.count)
    result = conn.get_list(rsp_count)
    if result:
        ip_list= [p.decode('utf-8') for p in result]
        rsp_count = len(ip_list)
    else:
        ip_list = []
        rsp_count = 0
    logger.debug('requested ip list count = {0} while return count = {1}'.format(req_count, rsp_count),
                 extra={'address': get_address(request), 'method': request.method})
    return Response(text=jsonify(ip_list), content_type='application/json')

async def get_count(request):
    """get proxy count in pool.

    return json data like: "{'count': 42, 'proxies': []}"
    """
    logger.debug('requested proxy pool count',
                 extra={'address': get_address(request), 'method': request.method})
    return Response(text=jsonify([], conn.count), content_type='application/json')

def get_address(request):
    peername = request.transport.get_extra_info('peername')
    if peername is not None:
        host, port = peername
        return '{0}:{1}'.format(host, port)

    return ''

def jsonify(ip, count=None):
    jsons = {}
    jsons['count'] = len(ip)
    jsons['proxies'] = ip

    if count:
        jsons['count'] = count

    return json.dumps(jsons)

def get_ssl_context():
    context = ssl.SSLContext()
    context.load_cert_chain(CERT, KEY, PASSWORD)
    if CA_CRT:
        context.load_verify_locations(CA_CRT)
    else:
        context.load_default_certs(ssl.Purpose.CLIENT_AUTH)
    context.verify_mode = ssl.CERT_OPTIONAL
    return context

def init(loop):
    app = Application(loop=loop)
    app.router.add_route('GET', '/', index)
    resource = app.router.add_resource(r'/proxies/{count:\d*}', name='proxy-get')
    resource.add_route('GET', get_ip_list)
    app.router.add_route('GET', '/proxies/count', get_count)
    app.router.add_static('/css/',
                          path=str(PROJECT_ROOT / 'static/css'),
                          name='css')
    app.router.add_static('/font/',
                          path=str(PROJECT_ROOT / 'static/font'),
                          name='font')
    if SSL_ON:
        ssl_context = get_ssl_context()
    else:
        ssl_context = None
    run_app(app, host=HOST, port=PORT, ssl_context=ssl_context)


def setup_cache(path, name, mtime, expire=-1):
    with open(path, 'r') as f:
        new = f.read()
    conn.set_cache(name, new, mtime, expire)


def server_run():
    loop = asyncio.get_event_loop()
    try:
        logger.debug('server started at http://{0}:{1}...'.format(HOST, PORT),
                     extra={'address': '', 'method': ''})
        # loop.run_until_complete(init(loop))
        # loop.run_forever()
        init(loop)
    except:
        logger.error(traceback.format_exc(), extra={'address': '', 'method': ''})
    finally:
        loop.close()


if __name__ == '__main__':
    server_run()
