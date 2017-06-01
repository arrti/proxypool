from proxypool.config import upper_limit, lower_limit, check_cycle_time, \
                              check_interval_time, validate_cycle_time, upper_limit_ratio
from proxypool.db import RedisClient as rc
from proxypool.proxy_crawler import ProxyCrawler
from proxypool.proxy_validator import ProxyValidator
from proxypool.utils import logger
import time
import asyncio
from random import random


class ProxyPool(object):


    @staticmethod
    async def crawler_start(crawler, validator, proxies, flag):
        """ Start proxy crawler and validator.

        Args:
            crawler: ProxyCrawler object.
            validator: ProxyValidator object.
            proxies: asyncio.Queue object, crawler put proxy and validator get proxy.
            flag: asyncio.Event object, stop flag for 'crawler_stop' function.
        """
        logger.debug('proxy crawler started')
        logger.debug('validator started')
        valid = asyncio.ensure_future(validator.start(proxies))
        await crawler.start()
        await proxies.join()
        valid.cancel() # cancel task when Queue was empty, or it would be blocked at Queue.get method

        flag.set()
        logger.debug('proxy crawler finished')

    # @staticmethod
    # def crawler_done(loop, future):
    #     logger.debug('event loop was stopping because {0}'.format(future.result()))
    #     # loop.stop()

    @staticmethod
    async def crawler_stop(crawler, conn, flag):
        """Check proxies count if enough to stop proxy crawler.

        Args:
            crawler: ProxyCrawler object.
            conn: redis connection.
            flag: asyncio.Event object, stop flag.
        """
        # await asyncio.sleep(10) # TODO
        while 1:

            if conn.count > int(upper_limit * upper_limit_ratio):
                logger.warning('proxies count approached the upper limit')
                crawler.stop()
                break
            if flag.is_set(): # stop check if crawler and validator finished
                break

            logger.debug('checked proxies count in redis')
            await asyncio.sleep(200 * random())

    @staticmethod
    def extend_proxy_pool():
        """Check proxies count if need to extend proxy pool.
        """
        conn = rc()
        loop = asyncio.get_event_loop()
        proxies = asyncio.Queue()
        crawler = ProxyCrawler(proxies)
        validator = ProxyValidator(conn)
        while 1:
            if conn.count > lower_limit:
                time.sleep(check_cycle_time)
                continue

            logger.debug('extend proxy pool started')
            flag = asyncio.Event()
            try:
                loop.run_until_complete(asyncio.gather(
                    ProxyPool.crawler_start(crawler, validator, proxies, flag),
                    ProxyPool.crawler_stop(crawler, conn, flag)
                ))
            except Exception as e:
                logger.error(e, exc_info=True)

            logger.debug('extend proxy pool finished')
            time.sleep(check_interval_time)
            crawler.reset() # create new flag


def proxy_pool_run():
    ProxyPool.extend_proxy_pool()


if __name__ == "__main__":
    proxy_pool_run()
