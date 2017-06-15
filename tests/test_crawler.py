import asyncio
from multiprocessing import Process, Value
from ctypes import c_int

import pytest

from proxypool.proxy_crawler import proxy_crawler_test_run


phantomjs = pytest.mark.skipif(
    not pytest.config.getoption("--runptjs"),
    reason="need --runptjs option to run"
)

class TestRule(object):
    start_url =  'http://www.xicidaili.com/nn/'
    page_count = 2
    urls_format = '{0}{1}'
    next_page_xpath = '//div[@class="pagination"]/a[@class="next_page"]/@href'
    next_page_host = 'http://www.xicidaili.com'

    use_phantomjs = False
    phantomjs_load_flag = None

    __rule_name__ = 'testrule'

    filters = None

    ip_xpath   = '//td[2]'
    port_xpath = '//td[3]'


def test_proxy_crawler():
    queue = asyncio.Queue()
    rule1 = TestRule()
    rule2 = TestRule()
    rule2.urls_format = None

    count = Value(c_int)

    crawler = Process(target=proxy_crawler_test_run, args=(queue, count, (rule1, rule2)))
    crawler.start()
    crawler.join()
    assert count.value > 0
    assert count.value == 400

@phantomjs
def test_proxy_crawler_phantomjs():
    queue = asyncio.Queue()
    rule = TestRule()
    rule.use_phantomjs = True
    rule.phantomjs_load_flag = '<table id="ip_list">'

    count = Value(c_int)

    crawler = Process(target=proxy_crawler_test_run, args=(queue, count, (rule, )))
    crawler.start()
    crawler.join()
    assert count.value > 0
    assert count.value == 200

