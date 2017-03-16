from proxypool.config import validate_upper_limit, validate_ratio, \
                             validate_cycle_time, validate_timeout
from proxypool.db import RedisClient as rc
from proxypool.utils import logger
import asyncio
import aiohttp
from math import ceil
import time


class ProxyValidator(object):
    """Validate proxy before put it in proxy pool and validate proxies in pool regularly.
    """

    def __init__(self, conn, flag=None):
        self.validate_url = 'http://www.baidu.com/' # without headers should visit 'http://' not 'https://'
        # self._stop_flag = flag if flag else asyncio.Event()
        self._conn = conn

    async def validate(self, proxies):
        logger.debug('validator started')
        while 1:
            proxy = await proxies.get()
            async with aiohttp.ClientSession() as session:
                try:
                    real_proxy = 'http://' + proxy
                    async with session.get(self.validate_url, proxy=real_proxy, timeout=validate_timeout) as resp:
                        self._conn.put(proxy)
                except Exception as e:
                    logger.error(e)

            proxies.task_done()

    async def regular_validate(self):
        count = min(ceil(self._conn.count * validate_ratio), validate_upper_limit)
        old_proxies = self._conn.get_list(count) # TODO: set an upper limit
        valid_proxies = []
        logger.debug('regular validator started, {0} to validate'.format(len(old_proxies)))
        async with aiohttp.ClientSession() as session:
            for proxy in old_proxies:
                try:
                    real_proxy = 'http://' + proxy.decode('utf-8') # proxy from redis was bytes type
                    async with session.get(self.validate_url, proxy=real_proxy, timeout=validate_timeout) as resp:
                        valid_proxies.append(proxy)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(e)

        logger.debug('regular validator finished, {0} passed'.format(len(valid_proxies)))
        self._conn.put_list(valid_proxies)

    async def start(self, proxies=None):
        if proxies:
            await self.validate(proxies)
        else:
            await self.regular_validate()


def proxy_validator_run():
    conn = rc()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    validator = ProxyValidator(conn)
    while 1:
        try:
            loop.run_until_complete(validator.start())
        except Exception as e:
            logger.error(e, exc_info=True)
        time.sleep(validate_cycle_time)


if __name__ == '__main__':
    proxy_validator_run()
