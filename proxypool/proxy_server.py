from proxypool.db import RedisClient as rc
from proxypool.config import host, port
from proxypool.utils import PROJECT_ROOT
import logging
import logging.config
import yaml
import asyncio
from aiohttp import web
import os.path


conn = rc()
logging.config.dictConfig(yaml.load(open(str(PROJECT_ROOT / 'logging.yaml'), 'r')))
logger = logging.getLogger('server_logger')

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
    return web.Response(body=cache, content_type='text/html')

async def get_ip(request):
    logger.debug('requested ip',
                 extra={'address': get_address(request), 'method': request.method})
    try:
        ip = conn.get()
    except Exception as e:
        ip = ''
        logger.error(e,
                     extra={'address': get_address(request), 'method': request.method})

    return web.Response(text=ip.decode('utf-8')) # bytes type data from redis

async def get_ip_list(request):
    req_count = request.match_info['count']
    rsp_count = min(int(req_count), conn.count) # TODO: set an upper limit
    result = conn.get_list(rsp_count)
    if result:
        ip_list= [p.decode('utf-8') for p in result]
        rsp_count = len(ip_list)
    else:
        ip_list = []
        rsp_count = 0
    logger.debug('requested ip list count = {0} while return count = {1}'.format(req_count, rsp_count),
                 extra={'address': get_address(request), 'method': request.method})
    return web.Response(text=str(ip_list))

async def get_count(request):
    logger.debug('requested proxy pool count',
                 extra={'address': get_address(request), 'method': request.method})
    return web.Response(text=str(conn.count))

def get_address(request):
    peername = request.transport.get_extra_info('peername')
    if peername is not None:
        host, port = peername
        return '{0}:{1}'.format(host, port)

    return ''

async def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', index)
    app.router.add_route('GET', '/get', get_ip)
    app.router.add_route('GET', '/get/{count}', get_ip_list)
    app.router.add_route('GET', '/count', get_count)
    app.router.add_static('/css/',
                          path=str(PROJECT_ROOT / 'static/css'),
                          name='css')
    app.router.add_static('/font/',
                          path=str(PROJECT_ROOT / 'static/font'),
                          name='font')
    srv = await loop.create_server(app.make_handler(), host, port)
    return srv

def setup_cache(path, name, mtime, expire=-1):
    with open(path, 'r') as f:
        new = f.read()
    conn.set_cache(name, new, mtime, expire)


def server_run():
    loop = asyncio.get_event_loop()
    try:
        logger.debug('server started at http://{0}:{1}...'.format(host, port),
                     extra={'address': '', 'method': ''})
        loop.run_until_complete(init(loop))
        loop.run_forever()
    finally:
        loop.close()


if __name__ == '__main__':
    server_run()
