
class ProxyPoolError(Exception):
    """proxypool error base"""


class CrawlerRuleImplementionError(ProxyPoolError):

    def __str__(self):
        return 'crawler rule required "start_url", "ip_xpath" and "port_xpath".'


class CrawlerRuleBaseInstantiateError(ProxyPoolError):

    def __str__(self):
        return "crawler rule base class shouldn't be instantiated."



class ProxyPoolEmptyError(ProxyPoolError):

    def __str__(self):
        return 'the proxy pool was empty in a long time.'
