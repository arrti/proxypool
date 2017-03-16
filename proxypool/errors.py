
class CrawlerRuleImplementionError(Exception):

    def __init__(self):
        super().__init__()

    def __str__(self):
        return 'crawler rule required "start_url", "ip_xpath" and "port_xpath".'

class CrawlerRuleBaseInstantiateError(Exception):

    def __init__(self):
        super().__init__()

    def __str__(self):
        return "crawler rule base class shouldn't be instantiated."


class ProxyPoolEmptyError(Exception):

    def __init__(self):
        super().__init__()

    def __str__(self):
        return 'the proxy pool was empty in a long time.'
