import redis

from proxypool.config import REDIS_HOST, REDIS_PORT
from proxypool.errors import ProxyPoolEmptyError


class RedisClient(object):
    """Redis manager class.

    Manage proxies and proxy server's html files cache with redis.
    """

    def __init__(self, host=REDIS_HOST, port=REDIS_PORT):
        self._db = redis.Redis(host=host, port=port)

    def pop(self):
        """Pop one proxy from pool.

        Returns:
             byte type proxy, like: b'175.155.24.67:808'.

        Raises:
            ProxyPoolEmptyError.
        """

        try:
            # timeout return None, otherwise return bytes type
            proxy = self._db.blpop('proxy_pool', 30)[1]
            self._db.srem('proxy_set', proxy)
            return proxy
        except TypeError:
            raise ProxyPoolEmptyError from None

    def pop_list(self, count=1):
        """Pop proxy list from pool.

        Args:
            the length of proxy list.

        Returns:
            proxy list, like: [b'175.155.24.67:808', b'112.103.59.215:8118'].
        """

        proxies = self._db.lrange('proxy_pool', 0, count - 1)
        self._db.ltrim('proxy_pool', count, -1)
        if proxies:
            self._db.srem('proxy_set', *proxies)
        return proxies

    def get(self):
        proxy = self.pop()
        self.put(proxy)

        return proxy

    def get_list(self, count=1):
        if count <= 0:
            return None

        proxies = self.pop_list(count)
        if proxies:
            self.put_list(proxies)
        return proxies

    def put(self, proxy):
        if self._db.sadd('proxy_set', proxy): # use set to avoid duplication
            self._db.rpush('proxy_pool', proxy)

    def put_list(self, proxies):
        for proxy in proxies:
            self.put(proxy)

    def set_cache(self, name, cache, mtime, expire=-1):
        """Set cache or update expire time according to modify time.

        Args:
            name: cache's name.
            cache: cache's content.
            mtime: modify time of cache's source file.
            expire: expire time in second, negative number for never expired.
        """

        mtime_name = '{0}_mtime'.format(name)
        old = self._db.get(mtime_name)
        if mtime != old:
            self._db.set(name, cache)
            self._db.set(mtime_name, mtime)
        if expire < 0:
            self._db.persist(name)
            self._db.persist(mtime_name)
        else:
            self._db.expire(name, expire)
            self._db.expire(mtime_name, expire)

    def get_cache(self, name):
        mtime_name = '{0}_mtime'.format(name)
        return self._db.get(name), self._db.get(mtime_name)

    @property
    def count(self):
        return self._db.llen('proxy_pool')
