from proxypool.config import (validate_upper_limit, validate_ratio,
                              validate_cycle_time, validate_timeout, CORO_COUNT)
from proxypool.db import RedisClient as rc
from proxypool.utils import logger
import asyncio
import aiohttp
from math import ceil
import time


class ProxyValidator(object):
    """Validate proxy before put it in proxy pool and validate proxies in pool regularly.
    """

    def __init__(self, conn):
        self.validate_url = 'http://www.baidu.com/' # without headers should visit 'http://' not 'https://'
        # self._stop_flag = flag if flag else asyncio.Event()
        self._conn = conn


    async def _validator(self, proxy):
        async with aiohttp.ClientSession() as session:
            try:
                real_proxy = 'http://' + proxy
                async with session.get(self.validate_url, proxy=real_proxy, timeout=validate_timeout) as resp:
                    self._conn.put(proxy)
            except asyncio.TimeoutError:
                pass
            except Exception as e:
                logger.error(e)

    async def validate_many(self, proxies):
        while 1:
            proxy = await proxies.get()
            await self._validator(proxy)
            proxies.task_done()

    async def _get_proxies(self):
        count = min(ceil(self._conn.count * validate_ratio), validate_upper_limit)
        old_proxies = self._conn.get_list(count)
        valid_proxies = asyncio.Queue()
        for proxy in old_proxies:
            await valid_proxies.put(proxy.decode('utf-8'))

        return valid_proxies

    async def validate_one(self, proxies):
        proxy = await proxies.get()
        await self._validator(proxy)
        proxies.task_done()

    async def start(self, proxies=None):
        if proxies is not None:
            to_validate = [self.validate_many(proxies) for _ in range(CORO_COUNT)]
        else:
            proxies = await self._get_proxies()
            to_validate = [self.validate_one(proxies) for _ in range(proxies.qsize())]

        await asyncio.wait(to_validate)


def proxy_validator_run():
    conn = rc()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    validator = ProxyValidator(conn)
    while 1:
        logger.debug('regular validator started')
        try:
            loop.run_until_complete(validator.start())
        except Exception as e:
            logger.error(e, exc_info=True)
        logger.debug('regular validator finished')
        time.sleep(validate_cycle_time)


if __name__ == '__main__':
    proxy_validator_run()
