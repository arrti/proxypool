import asyncio
from multiprocessing import Process, Value
from ctypes import c_int
from pathlib import Path
import os
import signal

from aiohttp.web import Application, Response, run_app
import pytest

from proxypool.proxy_crawler import proxy_crawler_test_run
from proxypool.config import HOST, PORT


phantomjs = pytest.mark.skipif(
    not pytest.config.getoption("--runptjs"),
    reason="need --runptjs option to run"
)

@pytest.fixture(scope='module')
def rule():
    TESTS_PATH = Path(__file__).parent

    class TestRule:
        start_url = 'http://{}:{}/nn/'.format(HOST, PORT)
        page_count = 3
        urls_format = '{0}{1}'
        next_page_xpath = '//div[@class="pagination"]/a[@class="next_page"]/@href'
        next_page_host = 'http://{}:{}'.format(HOST, PORT)

        use_phantomjs = False
        phantomjs_load_flag = None

        __rule_name__ = 'testrule'

        filters = None

        ip_xpath = '//td[2]'
        port_xpath = '//td[3]'

    async def proxy(request):
        page = request.match_info['page']
        if not page:
            path = '{}/pages/page_1.html'.format(TESTS_PATH)
        else:
            path = '{}/pages/page_{}.html'.format(TESTS_PATH, page)

        page = b"<html><body><pre>404: Not Found</pre></body></html>"
        try:
            with open(path, 'rb') as f:
                page = f.read()
        except:
            return Response(status=404, reason='Not Found', body=page, content_type='text/html')
        else:
            return Response(body=page, content_type='text/html')

    def start():
        app = Application()
        resource = app.router.add_resource(r'/nn/{page:\d*}', name='proxy-get')
        resource.add_route('GET', proxy)
        run_app(app, host=HOST, port=PORT)

    server = Process(target=start)
    server.start()

    yield TestRule

    os.kill(server.pid, signal.SIGINT)
    server.join()


def test_proxy_crawler(rule):
    queue = asyncio.Queue()
    rule1 = rule()
    rule2 = rule()
    rule2.urls_format = None

    count = Value(c_int)

    crawler = Process(target=proxy_crawler_test_run, args=(queue, count, (rule1, rule2)))
    crawler.start()
    crawler.join()
    assert count.value > 0
    assert count.value == 400

@phantomjs
def test_proxy_crawler_phantomjs(rule):
    queue = asyncio.Queue()
    rule = rule()
    rule.use_phantomjs = True
    rule.phantomjs_load_flag = '<table id="ip_list">'

    count = Value(c_int)

    crawler = Process(target=proxy_crawler_test_run, args=(queue, count, (rule, )))
    crawler.start()
    crawler.join()
    assert count.value > 0
    assert count.value == 200

