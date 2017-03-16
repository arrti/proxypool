from proxypool.errors import CrawlerRuleImplementionError, CrawlerRuleBaseInstantiateError


class CrawlerRuleMeta(type):
    """Meta class for manage crawler rules.

    Raises:
        CrawlerRuleImplementionError, TypeError.
    """

    def __new__(mcls, name, bases, namespace):
        if ('start_url' not in namespace or
            'ip_xpath' not in namespace or
            'port_xpath' not in namespace):
            raise CrawlerRuleImplementionError

        if (namespace.get('page_count', 0) > 1 and
            not namespace.get('urls_format', None) and
            not namespace.get('next_page_xpath', None)):
            raise TypeError('When "page_count" > 1, "urls_format" or "next_page_xpath" should be defined')

        if (namespace.get('use_phantomjs', False) and
            not namespace.get('phantomjs_load_flag', None)):
            raise TypeError('"Phantomjs_load_flag" should be set to indicate page was loaded')

        _filters_count = len(namespace.get('filters', ()))
        _filters_xpath_count = len(namespace.get('filters_xpath', ()))
        if (_filters_count != _filters_xpath_count):
            raise TypeError('The count of "filters"(={0}) and '
                            '"filters_xpath"(={1}) should be equal'.format(_filters_count, _filters_xpath_count))

        namespace['__rule_name__'] = name.lower()

        return super().__new__(mcls, name, bases, namespace)

class CrawlerRuleBase(object, metaclass=CrawlerRuleMeta):
    """Base class for each crawler rule.

    Used for 'ProxyCrawler' to traverse crawler rules(add new rule in '__init__.py' before it can be traversed).
    Don't instantiate this class.

    Raises:
        CrawlerRuleBaseInstantiateError.
    """

    start_url = None
    page_count = 0
    urls_format = None
    next_page_xpath = None
    next_page_host = ''

    use_phantomjs = False
    phantomjs_load_flag = None

    filters = ()

    ip_xpath = None
    port_xpath = None
    filters_xpath = ()

    def __init__(self):
        raise CrawlerRuleBaseInstantiateError
