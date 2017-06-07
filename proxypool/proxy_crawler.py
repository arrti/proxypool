import asyncio
from itertools import compress
import traceback

from proxypool.rules.rule_base import CrawlerRuleBase
from proxypool.utils import page_download, page_download_phantomjs, logger, Result


class ProxyCrawler(object):
    """Crawl proxies according to the rules."""

    def __init__(self, proxies, rules=None):
        """Crawler init.
        Args:
            proxies: aysncio.Queue object
            rules: crawler rules of each proxy web, should be iterable object
            flag: stop flag for page downloading
        """

        self._proxies = proxies
        self._stop_flag = asyncio.Event() # stop flag for crawler, not for validator
        self._pages = asyncio.Queue()
        self._rules = rules if rules else CrawlerRuleBase.__subclasses__()

    async def _parse_page(self):
        while 1:
            page = await self._pages.get()

            await self._parse_proxy(page.rule, page.content)

            self._pages.task_done()

    async def _parse_proxy(self, rule, page):
        ips = page.xpath(rule.ip_xpath)
        ports = page.xpath(rule.port_xpath)

        if not ips or not ports:
            logger.warning('{2} crawler could not get ip(len={0}) or port(len={1}), please check the xpaths or network'.
                  format(len(ips), len(ports), rule.__rule_name__))
            return

        proxies = map(lambda x, y: '{0}:{1}'.format(x.text.strip(), y.text.strip()), ips, ports)

        if rule.filters: # filter proxies
            filters = []
            for i, ft in enumerate(rule.filters_xpath):
                field = page.xpath(ft)
                if not field:
                    logger.warning('{1} crawler could not get {0} field, please check the filter xpath'.
                          format(rule.filters[i], rule.__rule_name__))
                    continue
                filters.append(map(lambda x: x.text.strip(), field))

            filters = zip(*filters)
            selector = map(lambda x: x == rule.filters, filters)
            proxies = compress(proxies, selector)

        for proxy in proxies:
            await self._proxies.put(proxy) # put proxies in Queue to validate

    @staticmethod
    def _url_generator(rule):
        """Url generator of next page.

        Returns:
            url of next page, like: 'http://www.example.com/page/2'.
        """

        page = yield Result(rule.start_url, rule)
        for i in range(2, rule.page_count + 1):
            if rule.urls_format:
                yield
                yield Result(rule.urls_format.format(rule.start_url, i), rule)
            elif rule.next_page_xpath:
                if page is None:
                    break
                next_page = page.xpath(rule.next_page_xpath)
                if next_page:
                    yield
                    page = yield Result(rule.next_page_host + str(next_page[0]).strip(), rule)
                else:
                    break

    async def _parser(self, count):
        to_parse = [self._parse_page() for _ in range(count)]
        await asyncio.wait(to_parse)

    async def _downloader(self, rule):
        if not rule.use_phantomjs:
            await page_download(ProxyCrawler._url_generator(rule), self._pages,
                                self._stop_flag)
        else:
            await page_download_phantomjs(ProxyCrawler._url_generator(rule), self._pages,
                                          rule.phantomjs_load_flag, self._stop_flag)

    async def _crawler(self, rule):
        logger.debug('{0} crawler started'.format(rule.__rule_name__))

        parser = asyncio.ensure_future(self._parser(rule.page_count))
        await self._downloader(rule)
        await self._pages.join()
        parser.cancel()

        logger.debug('{0} crawler finished'.format(rule.__rule_name__))

    async def start(self):
        to_crawl = [self._crawler(rule) for rule in self._rules]
        await asyncio.wait(to_crawl)

    def stop(self):
        self._stop_flag.set() # set crawler's stop flag
        logger.warning('proxy crawler was stopping...')

    def reset(self):
        self._stop_flag = asyncio.Event() # once setted, create a new Event object
        logger.debug('proxy crawler reseted')


def proxy_crawler_run(proxies, rules = None):
    pc = ProxyCrawler(proxies, rules)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(pc.start())
    except:
        logger.error(traceback.format_exc())
    finally:
        loop.close()

def proxy_crawler_test_run(proxies, count, rules = None):
    pc = ProxyCrawler(proxies, rules)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(pc.start())
        count.value = proxies.qsize()
    except:
        logger.error(traceback.format_exc())
    finally:
        loop.close()


if __name__ == '__main__':
    proxies = asyncio.Queue()
    proxy_crawler_run(proxies)
