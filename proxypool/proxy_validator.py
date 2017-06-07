import asyncio
from math import ceil
import time
import traceback

import aiohttp

from proxypool.config import (VALIDATE_UPPER_LIMIT, VALIDATE_RATIO,
                              VALIDATE_CYCLE_TIME, VALIDATE_TIMEOUT, CORO_COUNT)
from proxypool.ext import conn
from proxypool.utils import logger


class ProxyValidator(object):
    """Validate proxy before put it in proxy pool and proxies in pool regularly."""

    def __init__(self):
        self.validate_url = 'http://www.baidu.com/' # without headers should visit 'http://' not 'https://'

    async def _validator(self, proxy):
        async with aiohttp.ClientSession() as session:
            try:
                real_proxy = 'http://' + proxy
                async with session.get(self.validate_url, proxy=real_proxy, timeout=VALIDATE_TIMEOUT) as resp:
                    conn.put(proxy)
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
        count = min(ceil(conn.count * VALIDATE_RATIO), VALIDATE_UPPER_LIMIT)
        old_proxies = conn.get_list(count)
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
            if not to_validate:
                return

        await asyncio.wait(to_validate)


def proxy_validator_run():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    validator = ProxyValidator()
    while 1:
        logger.debug('regular validator started')
        try:
            loop.run_until_complete(validator.start())
        except Exception:
            logger.error(traceback.format_exc())
        logger.debug('regular validator finished')
        time.sleep(VALIDATE_CYCLE_TIME)


if __name__ == '__main__':
    proxy_validator_run()
